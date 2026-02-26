from __future__ import annotations

from flask.testing import FlaskClient

from app.db import repository


def _login_professor(client: FlaskClient, *, euid: str = "pro1234", password: str = "password123") -> str:
    r = client.post("/auth/login", json={"euid": euid, "password": password})
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"
    return data["access_token"]


def _seed_classes(app, *, owner_euid: str, codes: list[str]) -> None:
    with app.app_context():
        from app.db.connection import get_db

        db = get_db()
        for c in codes:
            repository.insert_class_info(
                db,
                code=c,
                professor_euid=owner_euid,
                lat=33.0,
                lon=-97.0,
                start_date="2026-02-01",
                end_date="2026-05-01",
            )
        db.commit()


def test_get_classes_me_paginates_and_filters_by_owner(app, client: FlaskClient) -> None:
    _seed_classes(app, owner_euid="pro1234", codes=["c1", "c2", "c3"])
    _seed_classes(app, owner_euid="pro9999", codes=["other1"])

    token = _login_professor(client, euid="pro1234")

    r = client.get(
        "/classes/me?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2
    assert data["classes"] == ["c1", "c2"]

    r2 = client.get(
        "/classes/me?page=2&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    data2 = r2.get_json()
    assert data2["classes"] == ["c3"]


def test_old_professor_classes_route_is_alias(app, client: FlaskClient) -> None:
    _seed_classes(app, owner_euid="pro1234", codes=["z1", "z2"])
    token = _login_professor(client, euid="pro1234")

    r = client.get(
        "/professors/pro1234/classes?page=1&page_size=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.headers.get("Deprecation") == "true"
    data = r.get_json()
    assert data["status"] == "success"
    assert data["classes"] == ["z1"]
    assert data["total"] == 2