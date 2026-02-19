def test_post_attendance_validation_error(client):
    resp = client.post("/attendance", json={})
    assert resp.status_code == 400
    assert resp.json["status"] == "error"
