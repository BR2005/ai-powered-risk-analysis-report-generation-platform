from app.schemas.assessment import AssessmentCreateRequest


def test_get_frameworks(client):
    response = client.get("/api/v1/frameworks")
    assert response.status_code == 200
    data = response.json()
    assert "frameworks" in data
    assert data["total_frameworks"] >= 10
    assert data["total_controls"] > 20

    ids = [fw["id"] for fw in data["frameworks"]]
    assert "OWASP-GENAI" in ids
    assert "OWASP-MCP" in ids
    assert "OWASP-AGENTIC" in ids
    assert "OWASP-WEB" in ids
    assert "OWASP-API" in ids
    assert "NIST-AI-RMF" in ids
    assert "MITRE-ATLAS" in ids
    assert "ISO-42001" in ids
    assert "ISO-23894" in ids
    assert "EU-AI-ACT" in ids

    for framework_id in ("OWASP-MCP", "OWASP-AGENTIC", "OWASP-WEB", "OWASP-API"):
        framework = next(item for item in data["frameworks"] if item["id"] == framework_id)
        assert framework["controls_count"] == 10
        assert len(framework["controls"]) == 10


def test_assessment_defaults_include_all_owasp_top10_frameworks():
    request = AssessmentCreateRequest(project_name="Framework defaults")
    selected_owasp = {
        framework_id
        for framework_id in request.target_frameworks
        if framework_id.startswith("OWASP-")
    }
    assert selected_owasp == {
        "OWASP-GENAI",
        "OWASP-MCP",
        "OWASP-AGENTIC",
        "OWASP-WEB",
        "OWASP-API",
    }
