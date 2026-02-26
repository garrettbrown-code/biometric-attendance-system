from __future__ import annotations

from flask.testing import FlaskClient

from app.db import repository


def _login_student(client: FlaskClient, *, euid: str = "stu1234", password: str = "password123") -> str:
    r = client.post("/auth/login", json={"euid": euid, "password": password})
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"
    return data["access_token"]


def _seed_class_with_sessions(app, *, code: str, professor_euid: str, start_date: str, end_date: str) -> None:
    # Create sessions on Monday + Wednesday at 10:00:00 in the date range.
    times = {"Monday": "10:00:00", "Wednesday": "10:00:00"}
    join_code = "ABCDEFGH"
    join_code_created_at = "2026-02-01T00:00:00+00:00"

    with app.app_context():
        from app.db.connection import get_db

        db = get_db()
        repository.add_class(
            db,
            code=code,
            professor_euid=professor_euid,
            lat=33.0,
            lon=-97.0,
            start_date=start_date,
            end_date=end_date,
            times=times,
            join_code=join_code,
            join_code_created_at=join_code_created_at,
        )
        db.commit()


def _enroll(app, *, code: str, student_euid: str) -> None:
    with app.app_context():
        from app.db.connection import get_db

        db = get_db()
        repository.enroll_student(db, code=code, student_euid=student_euid)
        db.commit()


def test_upcoming_sessions_only_for_enrolled_classes(app, client: FlaskClient) -> None:
    # Student enrolled in class A, not in class B.
    _seed_class_with_sessions(app, code="class_a", professor_euid="pro1234", start_date="2026-02-01", end_date="2026-02-28")
    _seed_class_with_sessions(app, code="class_b", professor_euid="pro1234", start_date="2026-02-01", end_date="2026-02-28")
    _enroll(app, code="class_a", student_euid="stu1234")

    token = _login_student(client, euid="stu1234")

    r = client.get(
        "/students/me/sessions/upcoming?from_date=2026-02-01&to_date=2026-02-28&page=1&page_size=100",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"

    # Ensure every returned session is for class_a only.
    assert all(s["code"] == "class_a" for s in data["sessions"])
    assert data["from_date"] == "2026-02-01"
    assert data["to_date"] == "2026-02-28"


def test_upcoming_sessions_paginates(app, client: FlaskClient) -> None:
    _seed_class_with_sessions(app, code="class_p", professor_euid="pro1234", start_date="2026-02-01", end_date="2026-03-15")
    _enroll(app, code="class_p", student_euid="stu1234")

    token = _login_student(client, euid="stu1234")

    r1 = client.get(
        "/students/me/sessions/upcoming?from_date=2026-02-01&to_date=2026-03-15&page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1["status"] == "success"
    assert d1["page"] == 1
    assert d1["page_size"] == 2
    assert d1["total"] >= 3
    assert d1["total_pages"] >= 2
    assert len(d1["sessions"]) == 2

    r2 = client.get(
        "/students/me/sessions/upcoming?from_date=2026-02-01&to_date=2026-03-15&page=2&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert d2["status"] == "success"
    assert d2["page"] == 2
    assert len(d2["sessions"]) >= 1

    # Ordering should be stable (date/time/code).
    first_page_last = d1["sessions"][-1]
    second_page_first = d2["sessions"][0]
    assert (second_page_first["session_date"], second_page_first["session_time"], second_page_first["code"]) >= (
        first_page_last["session_date"],
        first_page_last["session_time"],
        first_page_last["code"],
    )