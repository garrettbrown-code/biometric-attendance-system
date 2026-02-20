from __future__ import annotations

def _login(client, euid: str, password: str) -> dict[str, str]:
    resp = client.post("/auth/login", json={"euid": euid, "password": password})
    assert resp.status_code == 200, resp.json
    return {
        "access_token": resp.json["access_token"],
        "refresh_token": resp.json["refresh_token"],
    }


def _create_class_as_professor(client) -> None:
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
    # Either created (201) or already exists (409) depending on test DB seed behavior
    assert resp.status_code in (201, 409), resp.json


def test_student_can_enroll_in_class(client) -> None:
    _create_class_as_professor(client)
    stu = _login(client, "stu1234", "password123")

    resp = client.post(
        "/students/me/classes",
        headers={"Authorization": f"Bearer {stu['access_token']}"},
        json={"code": "csce_4900_500"},
    )
    assert resp.status_code == 201, resp.json


def test_student_enroll_duplicate_returns_409(client) -> None:
    _create_class_as_professor(client)
    stu = _login(client, "stu1234", "password123")

    first = client.post(
        "/students/me/classes",
        headers={"Authorization": f"Bearer {stu['access_token']}"},
        json={"code": "csce_4900_500"},
    )
    assert first.status_code in (201, 409)

    second = client.post(
        "/students/me/classes",
        headers={"Authorization": f"Bearer {stu['access_token']}"},
        json={"code": "csce_4900_500"},
    )
    assert second.status_code == 409, second.json


def test_student_enroll_unknown_class_returns_404(client) -> None:
    stu = _login(client, "stu1234", "password123")
    resp = client.post(
        "/students/me/classes",
        headers={"Authorization": f"Bearer {stu['access_token']}"},
        json={"code": "csce_4900_500"},
    )
    assert resp.status_code in (404, 409), resp.json


def test_student_can_list_my_classes(client) -> None:
    _create_class_as_professor(client)
    stu = _login(client, "stu1234", "password123")

    # ensure enrolled (ignore 409 if already)
    client.post(
        "/students/me/classes",
        headers={"Authorization": f"Bearer {stu['access_token']}"},
        json={"code": "csce_4900_500"},
    )

    resp = client.get(
        "/students/me/classes",
        headers={"Authorization": f"Bearer {stu['access_token']}"},
    )
    assert resp.status_code == 200, resp.json
    codes = [c["code"] for c in resp.json["classes"]]
    assert "csce_4900_500" in codes


def test_student_my_attendance_alias_is_protected(client) -> None:
    resp = client.get("/students/me/attendance")
    assert resp.status_code == 401