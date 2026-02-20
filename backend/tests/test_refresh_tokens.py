from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.auth.jwt_utils import create_refresh_token
from app.config import Config
from app.factory import create_app
from app.services.auth_service import register_user


@pytest.fixture()
def app_with_refresh(tmp_path: Path):
    """
    App configured to use a temp DB and test JWT settings.
    Expects schema.sql to include tbl_refresh_tokens.
    """
    app = create_app()
    app.config["TESTING"] = True

    db_path = tmp_path / "test_refresh.db"
    user_dir = tmp_path / "users"

    app.config["APP_CONFIG"] = Config(
        database_path=str(db_path),
        user_data_dir=user_dir,
        jwt_secret_key="test-secret-32-bytes-minimum-length!!",
        jwt_algorithm="HS256",
        jwt_exp_minutes=60,
        jwt_refresh_exp_days=7,
    )

    with app.app_context():
        from app.db.connection import init_db

        init_db()

        # Seed users
        register_user(euid="pro1234", password="password123", role="professor")
        register_user(euid="stu1234", password="password123", role="student")

    return app


@pytest.fixture()
def client(app_with_refresh):
    return app_with_refresh.test_client()


def _login(client, *, euid: str, password: str) -> dict[str, str]:
    resp = client.post("/auth/login", json={"euid": euid, "password": password})
    assert resp.status_code == 200, resp.json
    return {
        "access_token": resp.json["access_token"],
        "refresh_token": resp.json["refresh_token"],
    }


def test_login_returns_access_and_refresh(client) -> None:
    tokens = _login(client, euid="stu1234", password="password123")
    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_refresh_returns_new_token_pair(client) -> None:
    tokens = _login(client, euid="pro1234", password="password123")

    resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200, resp.json
    assert resp.json["status"] == "success"
    assert resp.json["access_token"]
    assert resp.json["refresh_token"]

    # Should rotate (new refresh token)
    assert resp.json["refresh_token"] != tokens["refresh_token"]


def test_refresh_old_token_is_revoked_after_rotation(client) -> None:
    tokens = _login(client, euid="stu1234", password="password123")

    first = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert first.status_code == 200, first.json
    assert first.json["refresh_token"]

    # Old refresh token should no longer work after rotation
    second = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert second.status_code == 401
    assert second.json["status"] == "error"


def test_refresh_missing_token_returns_400(client) -> None:
    resp = client.post("/auth/refresh", json={})
    assert resp.status_code == 400
    assert resp.json["status"] == "error"


def test_refresh_with_access_token_returns_401(client) -> None:
    tokens = _login(client, euid="stu1234", password="password123")
    # Passing an access token where refresh token is expected should fail
    resp = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401
    assert resp.json["status"] == "error"


def test_refresh_token_cannot_be_used_as_access_token(app_with_refresh, client) -> None:
    """
    Guardrail: sending a refresh token in Authorization header should not 500.
    It should be rejected as 401 (invalid token for this endpoint) or 403.
    """
    tokens = _login(client, euid="pro1234", password="password123")
    refresh = tokens["refresh_token"]

    resp = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {refresh}"},
        json={
            "code": "csce_4900_500",
            "euid": "pro1234",
            "location": [33.214, -97.133],
            "start_date": "2025-04-01",
            "end_date": "2025-04-15",
            "times": {"Monday": "09:00:00"},
        },
    )
    assert resp.status_code in (401, 403)
    assert resp.json["status"] == "error"


def test_refresh_rejected_if_token_marked_revoked(app_with_refresh, client) -> None:
    tokens = _login(client, euid="stu1234", password="password123")
    refresh = tokens["refresh_token"]

    # Mark refresh token revoked directly in DB
    with app_with_refresh.app_context():
        from app.db.connection import get_db

        db = get_db()
        db.execute(
            "UPDATE tbl_refresh_tokens SET fld_rt_revoked = 1 WHERE fld_rt_token = ?",
            (refresh,),
        )
        db.commit()

    resp = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 401
    assert resp.json["status"] == "error"


def test_refresh_rejected_if_token_expired(app_with_refresh, client) -> None:
    cfg: Config = app_with_refresh.config["APP_CONFIG"]

    # Create an already-expired refresh JWT
    expired_refresh = create_refresh_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject="stu1234",
        exp_days=-1,
    )

    # Insert it into DB as if issued (but with expired timestamp)
    with app_with_refresh.app_context():
        from app.db.connection import get_db

        db = get_db()
        past = datetime.now(timezone.utc) - timedelta(days=1)
        db.execute(
            """
            INSERT INTO tbl_refresh_tokens (fld_rt_euid, fld_rt_token, fld_rt_expires_at, fld_rt_revoked)
            VALUES (?, ?, ?, 0)
            """,
            ("stu1234", expired_refresh, past.isoformat()),
        )
        db.commit()

    resp = client.post("/auth/refresh", json={"refresh_token": expired_refresh})
    assert resp.status_code == 401
    assert resp.json["status"] == "error"


def test_refreshed_access_token_works_for_rbac(client) -> None:
    """
    Ensures refresh flow preserves role correctly.
    We'll refresh as professor and confirm new access token can create a class (prof-only).
    """
    tokens = _login(client, euid="pro1234", password="password123")

    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200, refreshed.json

    new_access = refreshed.json["access_token"]

    resp = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {new_access}"},
        json={
            "code": "csce_4901_501",
            "euid": "pro1234",
            "location": [33.214, -97.133],
            "start_date": "2025-04-01",
            "end_date": "2025-04-15",
            "times": {"Monday": "09:00:00"},
        },
    )
    assert resp.status_code == 201, resp.json
    assert resp.json["status"] == "success"