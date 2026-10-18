def test_health_check(client):
    response = client.get(
        "/health",
        headers={"Origin": "https://frontend.example"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "database" in data
    assert data["database"] == "connected"
