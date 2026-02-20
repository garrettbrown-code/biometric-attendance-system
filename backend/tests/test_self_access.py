from __future__ import annotations

import pytest


def _login(client, euid: str, password: str) -> dict[str, str]:
    resp = client.post("/auth/login", json={"euid": euid, "password": password})
    assert resp.status_code == 200, resp.json
    return {
        "access_token": resp.json["access_token"],
        "refresh_token": resp.json["refresh_token"],
    }


def test_student_cannot_access_other_student_attendance(client):
    tokens = _login(client, "stu1234", "password123")

    resp = client.get(
        "/students/stu9999/attendance",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert resp.status_code == 403


def test_professor_cannot_create_class_for_other_professor(client):
    tokens = _login(client, "pro1234", "password123")

    resp = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "code": "csce_9999_999",
            "euid": "pro9999",
            "location": [33.214, -97.133],
            "start_date": "2025-04-01",
            "end_date": "2025-04-15",
            "times": {"Monday": "09:00:00"},
        },
    )

    assert resp.status_code == 403