from datetime import datetime, timezone
from app.db.connection import get_db
from app.auth.password_utils import hash_password, verify_password
from app.auth.jwt_utils import create_access_token


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

    token = create_access_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject=euid,
        role=row["fld_us_role"],
        exp_minutes=cfg.jwt_exp_minutes,
    )
    return token