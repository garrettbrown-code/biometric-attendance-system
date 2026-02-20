from __future__ import annotations


def test_openapi_json_served(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    body = resp.get_json()
    assert isinstance(body, dict)
    assert body.get("openapi", "").startswith("3.")
    assert "paths" in body


def test_swagger_docs_served(client):
    # Swagger UI blueprint usually serves HTML and may redirect to a trailing slash.
    resp = client.get("/docs", follow_redirects=False)
    assert resp.status_code in (200, 301, 302, 308)