from __future__ import annotations

from pathlib import Path
import pytest

from app.config import Config
from app.factory import create_app


@pytest.fixture()
def app(tmp_path: Path):
    """
    Shared test app with seeded users for auth/RBAC tests.
    """
    app = create_app()
    app.config["TESTING"] = True

    db_path = tmp_path / "test.db"
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
        from app.services.auth_service import register_user

        init_db()

        # Seed baseline users used across test suites
        register_user(euid="pro1234", password="password123", role="professor")
        register_user(euid="stu1234", password="password123", role="student")
        # Extra users for self-access tests
        register_user(euid="pro9999", password="password123", role="professor")
        register_user(euid="stu9999", password="password123", role="student")

    return app


@pytest.fixture()
def client(app):
    return app.test_client()