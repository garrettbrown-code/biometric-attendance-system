from datetime import datetime, timedelta, timezone
import jwt


def create_access_token(*, secret: str, algorithm: str, subject: str, role: str, exp_minutes: int):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=exp_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, secret: str, algorithm: str):
    return jwt.decode(token, secret, algorithms=[algorithm])