from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
import sqlite3

from app.db.connection import get_db
from app.config import Config
from app.auth.password_utils import hash_password, verify_password
from app.auth.jwt_utils import create_access_token, create_refresh_token, decode_token
from app.db import repository
from app.services.face_service import save_reference_image, verify_face_match


def issue_token_pair(*, subject: str, role: str, cfg: Config, db: sqlite3.Connection) -> dict[str, str]:
    """
    Issues an access + refresh token pair and persists the refresh token in DB.
    Used by:
      - password login
      - student enroll (first-time setup)
      - student face login
    """
    access = create_access_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject=subject,
        role=role,
        exp_minutes=cfg.jwt_exp_minutes,
    )

    refresh = create_refresh_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject=subject,
        exp_days=cfg.jwt_refresh_exp_days,
    )

    expires = datetime.now(timezone.utc) + timedelta(days=int(cfg.jwt_refresh_exp_days))
    db.execute(
        """
        INSERT INTO tbl_refresh_tokens (fld_rt_euid, fld_rt_token, fld_rt_expires_at, fld_rt_revoked)
        VALUES (?, ?, ?, 0)
        """,
        (subject, refresh, expires.isoformat()),
    )
    db.commit()

    return {"access_token": access, "refresh_token": refresh}


def register_user(*, euid: str, password: str, role: str):
    db = get_db()
    hashed = hash_password(password)
    db.execute(
        """
        INSERT INTO tbl_users (fld_us_euid, fld_us_role, fld_us_password_hash, fld_us_created_at)
        VALUES (?, ?, ?, ?)
        """,
        (euid, role, hashed, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()


def refresh_access_token(*, refresh_token: str, cfg):
    """
    Validates a refresh token against JWT + DB, rotates it, and returns a new token pair.
    Returns None on failure.
    """
    db = get_db()

    # 1) Validate JWT signature/exp
    try:
        payload = decode_token(
            refresh_token,
            secret=cfg.jwt_secret_key,
            algorithm=cfg.jwt_algorithm,
        )
    except Exception:
        return None

    # 2) Must be a refresh token
    if payload.get("type") != "refresh":
        return None

    sub = payload.get("sub")
    if not sub:
        return None

    # 3) Must exist in DB + not revoked
    row = db.execute(
        """
        SELECT fld_rt_euid, fld_rt_expires_at, fld_rt_revoked
        FROM tbl_refresh_tokens
        WHERE fld_rt_token = ?
        """,
        (refresh_token,),
    ).fetchone()

    if not row:
        return None

    if int(row["fld_rt_revoked"]) == 1:
        return None

    # 4) Must not be expired per DB timestamp
    try:
        expires_at = datetime.fromisoformat(row["fld_rt_expires_at"])
    except Exception:
        return None

    if expires_at.tzinfo is None:
        # Defensive: assume UTC if tz missing
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        return None

    euid = row["fld_rt_euid"]

    # 5) Fetch role for new access token
    urow = db.execute(
        "SELECT fld_us_role FROM tbl_users WHERE fld_us_euid = ?",
        (euid,),
    ).fetchone()
    if not urow:
        return None
    role = urow["fld_us_role"]

    # 6) Rotate: revoke old refresh, issue new refresh + access, persist new refresh
    db.execute(
        "UPDATE tbl_refresh_tokens SET fld_rt_revoked = 1 WHERE fld_rt_token = ?",
        (refresh_token,),
    )

    new_access = create_access_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject=euid,
        role=role,
        exp_minutes=cfg.jwt_exp_minutes,
    )

    new_refresh = create_refresh_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject=euid,
        exp_days=cfg.jwt_refresh_exp_days,
    )

    new_expires = datetime.now(timezone.utc) + timedelta(days=int(cfg.jwt_refresh_exp_days))
    db.execute(
        """
        INSERT INTO tbl_refresh_tokens (fld_rt_euid, fld_rt_token, fld_rt_expires_at, fld_rt_revoked)
        VALUES (?, ?, ?, 0)
        """,
        (euid, new_refresh, new_expires.isoformat()),
    )
    db.commit()

    return {"access_token": new_access, "refresh_token": new_refresh}


def authenticate_user(*, euid: str, password: str, cfg):
    db = get_db()
    row = db.execute(
        "SELECT fld_us_password_hash, fld_us_role FROM tbl_users WHERE fld_us_euid = ?",
        (euid,),
    ).fetchone()

    if not row:
        return None

    if not verify_password(password, row["fld_us_password_hash"]):
        return None

    role = row["fld_us_role"]
    return issue_token_pair(subject=euid, role=role, cfg=cfg, db=db)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def enroll_student_with_join_code(
    *,
    db: sqlite3.Connection,
    cfg: Config,
    euid: str,
    code: str,
    join_code: str,
    photo_b64: str,
) -> dict[str, str] | None:
    # 1) join code must match class
    if not repository.verify_join_code(db, code=code, join_code=join_code):
        return None

    # 2) ensure student user exists (no password login, but tbl_users requires a hash)
    # create an unguessable random password hash so password login is effectively disabled for students
    random_secret = secrets.token_urlsafe(32)
    # assumes you already have a password hashing helper
    password_hash = hash_password(random_secret)  # <- existing helper in your file

    db.execute(
        """
        INSERT OR IGNORE INTO tbl_users (fld_us_euid, fld_us_role, fld_us_password_hash, fld_us_created_at)
        VALUES (?, 'student', ?, ?)
        """,
        (euid, password_hash, _now_iso()),
    )

    # 3) save reference image
    ref_path = cfg.user_data_dir / "Student" / euid / "reference_image.jpg"
    save_reference_image(photo_b64=photo_b64, dest_path=ref_path)

    # 4) enroll into class roster
    repository.enroll_student(db, code=code, student_euid=euid)
    db.commit()

    # 5) issue tokens (student role)
    return issue_token_pair(subject=euid, role="student", cfg=cfg, db=db)


def face_login_student(
    *,
    db: sqlite3.Connection,
    cfg: Config,
    euid: str,
    photo_b64: str,
) -> dict[str, str] | None:
    # Must exist as student user
    cur = db.execute(
        "SELECT fld_us_role AS role FROM tbl_users WHERE fld_us_euid = ? LIMIT 1",
        (euid,),
    )
    row = cur.fetchone()
    if not row or row["role"] != "student":
        return None

    ref_path = cfg.user_data_dir / "Student" / euid / "reference_image.jpg"
    result = verify_face_match(submitted_photo_b64=photo_b64, reference_image_path=ref_path)
    if result.status != "success":
        return None

    return issue_token_pair(subject=euid, role="student", cfg=cfg, db=db)