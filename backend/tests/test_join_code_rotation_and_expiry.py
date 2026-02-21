from __future__ import annotations

import base64
from io import BytesIO
from datetime import datetime, timedelta, timezone
from app.config import Config
from dataclasses import replace

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


def _create_class_get_join_code(client, app) -> str:
    pro = _login(client, "pro1234", "password123")
    resp = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {pro['access_token']}"},
        json={
            "code": "csce_4900_500",
            "euid": "pro1234",
            "location": [33.214, -97.133],
            "start_date": "2025-04-01",
            "end_date": "2025-04-15",
            "times": {"Monday": "09:00:00"},
        },
    )
    assert resp.status_code in (201, 409), resp.json

    if resp.status_code == 201:
        return resp.json["join_code"]

    # If already exists, read from DB
    with app.app_context():
        from app.db.connection import get_db
        from app.db import repository

        db = get_db()
        row = repository.get_join_code(db, code="csce_4900_500")
        assert row
        return row["join_code"]


def test_enroll_rejected_when_join_code_expired(client, app, monkeypatch) -> None:
    join_code = _create_class_get_join_code(client, app)

    # Force TTL to 1 hour for this test
    cfg = app.config["APP_CONFIG"]
    app.config["APP_CONFIG"] = replace(cfg, join_code_ttl_hours=1)

    # Backdate join code creation time by 2 hours => expired
    with app.app_context():
        from app.db.connection import get_db

        db = get_db()
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        db.execute(
            "UPDATE tbl_class_info SET fld_ci_join_code_created_at = ? WHERE fld_ci_code_pk = ?",
            (old, "csce_4900_500"),
        )
        db.commit()

    resp = client.post(
        "/auth/enroll",
        json={
            "euid": "stu9999",
            "code": "csce_4900_500",
            "join_code": join_code,
            "photo": _img_b64(),
        },
    )
    assert resp.status_code == 401, resp.json


def test_rotate_join_code_invalidates_old_code_and_accepts_new(client, app) -> None:
    pro = _login(client, "pro1234", "password123")
    old_code = _create_class_get_join_code(client, app)

    rotate = client.post(
        "/classes/csce_4900_500/join-code/rotate",
        headers={"Authorization": f"Bearer {pro['access_token']}"},
    )
    assert rotate.status_code == 200, rotate.json
    new_code = rotate.json["join_code"]
    assert new_code != old_code

    # Old code should fail enrollment
    bad = client.post(
        "/auth/enroll",
        json={"euid": "stu8888", "code": "csce_4900_500", "join_code": old_code, "photo": _img_b64()},
    )
    assert bad.status_code == 401, bad.json

    # New code should work
    ok = client.post(
        "/auth/enroll",
        json={"euid": "stu7777", "code": "csce_4900_500", "join_code": new_code, "photo": _img_b64()},
    )
    assert ok.status_code == 200, ok.json
    assert "access_token" in ok.json
    assert "refresh_token" in ok.json