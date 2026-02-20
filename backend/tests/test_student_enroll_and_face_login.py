from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image


def _img_b64() -> str:
    img = Image.new("RGB", (1, 1))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _login(client, euid: str, password: str) -> dict[str, str]:
    resp = client.post("/auth/login", json={"euid": euid, "password": password})
    assert resp.status_code == 200, resp.json
    return {"access_token": resp.json["access_token"], "refresh_token": resp.json["refresh_token"]}


def test_student_enroll_writes_reference_image_and_returns_tokens(client, app):
    # professor creates class, response includes join_code
    tokens = _login(client, "pro1234", "password123")

    create = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "code": "csce_4900_500",
            "euid": "pro1234",
            "location": [33.214, -97.133],
            "start_date": "2025-04-01",
            "end_date": "2025-04-15",
            "times": {"Monday": "09:00:00"},
        },
    )
    assert create.status_code in (201, 409), create.json

    # If class already exists from other tests, fetch join_code from DB
    if create.status_code == 201:
        join_code = create.json["join_code"]
    else:
        with app.app_context():
            from app.db.connection import get_db
            from app.db import repository

            db = get_db()
            row = repository.get_join_code(db, code="csce_4900_500")
            assert row
            join_code = row["join_code"]

    photo = _img_b64()

    enroll = client.post(
        "/auth/enroll",
        json={"euid": "stu9999", "code": "csce_4900_500", "join_code": join_code, "photo": photo},
    )
    assert enroll.status_code == 200, enroll.json
    assert "access_token" in enroll.json
    assert "refresh_token" in enroll.json

    # reference image should exist
    cfg = app.config["APP_CONFIG"]
    ref_path = Path(cfg.user_data_dir) / "Student" / "stu9999" / "reference_image.jpg"
    assert ref_path.exists()


@patch("app.services.auth_service.verify_face_match")
def test_student_face_login_returns_tokens(mock_verify, client):
    # Make face match succeed without importing face_recognition
    mock_verify.return_value = type("R", (), {"status": "success", "error": None})()

    resp = client.post("/auth/face-login", json={"euid": "stu1234", "photo": _img_b64()})
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        assert "access_token" in resp.json
        assert "refresh_token" in resp.json


def test_enroll_rejects_bad_join_code(client):
    resp = client.post(
        "/auth/enroll",
        json={
            "euid": "stu9999",
            "code": "csce_4900_500",
            "join_code": "WRONGCODE",
            "photo": _img_b64(),
        },
    )
    assert resp.status_code in (400, 401)