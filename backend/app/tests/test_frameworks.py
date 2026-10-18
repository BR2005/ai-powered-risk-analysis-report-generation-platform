def test_get_frameworks(client):
    response = client.get("/api/v1/frameworks")
    assert response.status_code == 200
    data = response.json()
    assert "frameworks" in data
    assert data["total_frameworks"] >= 6
    assert data["total_controls"] > 20

    ids = [fw["id"] for fw in data["frameworks"]]
    assert "OWASP-GENAI" in ids
    assert "NIST-AI-RMF" in ids
    assert "MITRE-ATLAS" in ids
    assert "ISO-42001" in ids
    assert "ISO-23894" in ids
    assert "EU-AI-ACT" in ids
