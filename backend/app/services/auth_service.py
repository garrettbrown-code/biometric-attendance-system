from __future__ import annotations

from datetime import datetime, timezone, timedelta
from app.db.connection import get_db
from app.auth.password_utils import hash_password, verify_password
from app.auth.jwt_utils import create_access_token, create_refresh_token, decode_token



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
    access = create_access_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject=euid,
        role=role,
        exp_minutes=cfg.jwt_exp_minutes,
    )

    refresh = create_refresh_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject=euid,
        exp_days=cfg.jwt_refresh_exp_days,
    )

    expires = datetime.now(timezone.utc) + timedelta(days=int(cfg.jwt_refresh_exp_days))
    db.execute(
        """
        INSERT INTO tbl_refresh_tokens (fld_rt_euid, fld_rt_token, fld_rt_expires_at, fld_rt_revoked)
        VALUES (?, ?, ?, 0)
        """,
        (euid, refresh, expires.isoformat()),
    )
    db.commit()

    return {"access_token": access, "refresh_token": refresh}