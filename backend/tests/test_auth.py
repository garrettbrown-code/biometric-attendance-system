# tests/test_auth.py
from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Config
from app.factory import create_app
from app.services.auth_service import register_user
from app.auth.jwt_utils import create_access_token


@pytest.fixture()
def app_with_auth(tmp_path: Path):
    """
    Creates an app configured to use a temp SQLite DB + test JWT settings,
    and initializes schema.
    """
    app = create_app()
    app.config["TESTING"] = True

    db_path = tmp_path / "test_auth.db"
    user_dir = tmp_path / "users"

    # Override config (Config is frozen, so replace the whole object)
    app.config["APP_CONFIG"] = Config(
        database_path=str(db_path),
        user_data_dir=user_dir,
        jwt_secret_key="test-secret-32-bytes-minimum-length!!",
        jwt_algorithm="HS256",
        jwt_exp_minutes=60,
    )

    # Initialize schema in temp DB
    with app.app_context():
        from app.db.connection import init_db

        init_db()

        # Seed two users
        register_user(euid="pro1234", password="password123", role="professor")
        register_user(euid="stu1234", password="password123", role="student")

    return app


@pytest.fixture()
def client(app_with_auth):
    return app_with_auth.test_client()


def _login(client, euid: str, password: str) -> str:
    resp = client.post("/auth/login", json={"euid": euid, "password": password})
    assert resp.status_code == 200, resp.json
    token = resp.json.get("access_token")
    assert token
    return token


def test_login_success_returns_token(client) -> None:
    resp = client.post("/auth/login", json={"euid": "stu1234", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json["status"] == "success"
    assert resp.json["access_token"]


def test_login_invalid_password_rejected(client) -> None:
    resp = client.post("/auth/login", json={"euid": "stu1234", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json["status"] == "error"
    assert "Invalid credentials" in resp.json["error"]


def test_protected_route_without_token_returns_401(client) -> None:
    resp = client.post("/classes", json={})
    assert resp.status_code == 401
    assert resp.json["status"] == "error"


def test_protected_route_wrong_role_returns_403(client) -> None:
    student_token = _login(client, "stu1234", "password123")

    # /classes requires professor
    resp = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "code": "csce_4900_500",
            "euid": "pro1234",
            "location": [33.214, -97.133],
            "start_date": "2025-04-01",
            "end_date": "2025-04-15",
            "times": {"Monday": "09:00:00"},
        },
    )
    assert resp.status_code == 403
    assert resp.json["status"] == "error"
    assert resp.json["error"] == "Forbidden"


def test_professor_can_create_class(client) -> None:
    prof_token = _login(client, "pro1234", "password123")

    resp = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {prof_token}"},
        json={
            "code": "csce_4900_500",
            "euid": "pro1234",
            "location": [33.214, -97.133],
            "start_date": "2025-04-01",
            "end_date": "2025-04-15",
            "times": {"Monday": "09:00:00", "Wednesday": "09:00:00"},
        },
    )
    assert resp.status_code == 201, resp.json
    assert resp.json["status"] == "success"
    assert resp.json["sessions_created"] > 0


def test_expired_token_returns_401(app_with_auth, client) -> None:
    cfg = app_with_auth.config["APP_CONFIG"]

    expired = create_access_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject="pro1234",
        role="professor",
        exp_minutes=-1,  # already expired
    )

    resp = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {expired}"},
        json={
            "code": "csce_4901_501",
            "euid": "pro1234",
            "location": [33.214, -97.133],
            "start_date": "2025-04-01",
            "end_date": "2025-04-15",
            "times": {"Monday": "09:00:00"},
        },
    )

    assert resp.status_code == 401
    assert resp.json["status"] == "error"
    assert "Invalid or expired token" in resp.json["error"]