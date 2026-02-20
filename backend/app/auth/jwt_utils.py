from __future__ import annotations
from datetime import datetime, timedelta, timezone
import uuid
import jwt


def create_access_token(*, secret: str, algorithm: str, subject: str, role: str, exp_minutes: int):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=exp_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_refresh_token(*, secret: str, algorithm: str, subject: str, exp_days: int):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(days=exp_days),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, secret: str, algorithm: str):
    return jwt.decode(token, secret, algorithms=[algorithm])