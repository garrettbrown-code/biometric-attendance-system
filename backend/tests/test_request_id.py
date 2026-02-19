def test_request_id_is_returned(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert resp.headers["X-Request-ID"]


def test_request_id_is_echoed(client):
    resp = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == "abc-123"
