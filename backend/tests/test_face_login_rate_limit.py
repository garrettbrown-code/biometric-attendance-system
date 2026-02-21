from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from collections import defaultdict
from unittest.mock import Mock

from PIL import Image


def _img_b64() -> str:
    """Create a tiny valid JPEG and return base64-encoded string."""
    img = Image.new("RGB", (1, 1))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _ensure_reference_image(app, euid: str) -> None:
    """Create a reference_image.jpg where face_login_student expects it."""
    cfg = app.config["APP_CONFIG"]
    ref_path = Path(cfg.user_data_dir) / "Student" / euid / "reference_image.jpg"
    ref_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (1, 1))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    ref_path.write_bytes(buf.getvalue())


def test_face_login_rate_limited_after_max_attempts(client, app, monkeypatch) -> None:
    """
    After MAX attempts within the window, the next request should be rate-limited.
    Our route currently returns 401 when face_login_student returns None.
    """
    import app.services.auth_service as auth_service

    # Reset attempt store for a clean test
    monkeypatch.setattr(auth_service, "_FACE_LOGIN_ATTEMPTS", defaultdict(list))

    # Make rate limit small for a fast test
    monkeypatch.setattr(auth_service, "_FACE_LOGIN_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(auth_service, "_FACE_LOGIN_WINDOW_SECONDS", 60)

    # Ensure the student exists in seeded DB and reference image exists
    euid = "stu1234"
    _ensure_reference_image(app, euid)

    # Patch verify_face_match to always fail (so attempts accumulate)
    mock_verify = Mock(return_value=type("R", (), {"status": "error", "error": "no match"})())
    monkeypatch.setattr(auth_service, "verify_face_match", mock_verify)

    payload = {"euid": euid, "photo": _img_b64()}

    # First 3 attempts: not rate-limited yet (still 401 because face mismatch)
    for _ in range(3):
        resp = client.post("/auth/face-login", json=payload)
        assert resp.status_code == 401

    # 4th attempt: should now be rate-limited (still 401 at the route level)
    resp = client.post("/auth/face-login", json=payload)
    assert resp.status_code == 401

    # verify_face_match should have been called only for the first 3 attempts.
    # The rate-limited attempt should short-circuit before face matching.
    assert mock_verify.call_count == 3


def test_face_login_rate_limit_is_per_user(client, app, monkeypatch) -> None:
    """
    Rate limit should be keyed per EUID, so one user's failures
    shouldn't block another user's login attempts.
    """
    import app.services.auth_service as auth_service

    monkeypatch.setattr(auth_service, "_FACE_LOGIN_ATTEMPTS", defaultdict(list))
    monkeypatch.setattr(auth_service, "_FACE_LOGIN_MAX_ATTEMPTS", 2)
    monkeypatch.setattr(auth_service, "_FACE_LOGIN_WINDOW_SECONDS", 60)

    _ensure_reference_image(app, "stu1234")
    _ensure_reference_image(app, "stu9999")

    mock_verify = Mock(return_value=type("R", (), {"status": "error", "error": "no match"})())
    monkeypatch.setattr(auth_service, "verify_face_match", mock_verify)

    p1 = {"euid": "stu1234", "photo": _img_b64()}
    p2 = {"euid": "stu9999", "photo": _img_b64()}

    # Exhaust stu1234's limit
    assert client.post("/auth/face-login", json=p1).status_code == 401
    assert client.post("/auth/face-login", json=p1).status_code == 401
    assert client.post("/auth/face-login", json=p1).status_code == 401  # now rate-limited

    # stu9999 should still get "normal" attempts (verify_face_match called)
    before = mock_verify.call_count
    assert client.post("/auth/face-login", json=p2).status_code == 401
    assert mock_verify.call_count == before + 1