from __future__ import annotations

from app.auth.jwt_utils import create_access_token
from app.config import Config


def test_post_attendance_requires_auth(client):
    resp = client.post("/attendance", json={})
    assert resp.status_code == 401
    assert resp.json["status"] == "error"


def test_post_attendance_validation_error_when_authenticated(app, client):
    """
    Once authenticated, invalid payloads should still return 400 (pydantic validation).
    """
    cfg: Config = app.config["APP_CONFIG"]
    token = create_access_token(
        secret=cfg.jwt_secret_key,
        algorithm=cfg.jwt_algorithm,
        subject="stu1234",
        role="student",
        exp_minutes=60,
    )

    resp = client.post(
        "/attendance",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert resp.status_code == 400
    assert resp.json["status"] == "error"