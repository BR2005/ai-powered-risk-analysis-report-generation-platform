from fastapi.testclient import TestClient

from app.main import app, fastapi_app


def test_health_check(client):
    response = client.get(
        "/health",
        headers={"Origin": "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "database" in data
    assert data["database"] == "connected"


def test_cors_preflight_allows_frontend_api_post(client):
    response = client.options(
        "/api/v1/assessments",
        headers={
            "Origin": "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "OPTIONS" in response.headers["access-control-allow-methods"]
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert "access-control-allow-credentials" not in response.headers


def test_cors_allows_local_development_origin(client):
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_does_not_allow_unconfigured_origins(client):
    response = client.get(
        "/health",
        headers={"Origin": "https://untrusted.example"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_cors_headers_are_added_to_error_responses(client):
    response = client.get(
        "/missing-route",
        headers={"Origin": "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"},
    )
    assert response.status_code == 404
    assert response.headers["access-control-allow-origin"] == "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"


def test_cors_headers_are_added_to_unhandled_server_errors():
    def raise_server_error():
        raise RuntimeError("test failure")

    fastapi_app.add_api_route(
        "/_test-unhandled-error",
        raise_server_error,
        methods=["GET"],
    )
    route = next(
        route for route in fastapi_app.router.routes
        if getattr(route, "path", None) == "/_test-unhandled-error"
    )
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            response = test_client.get(
                "/_test-unhandled-error",
                headers={"Origin": "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"},
            )
    finally:
        fastapi_app.router.routes.remove(route)

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"


def test_assessments_endpoint_returns_cors_header(client):
    response = client.get(
        "/api/v1/assessments",
        headers={"Origin": "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ai-powered-risk-analysis-report-generation-platform-6nhs2ch2j.vercel.app"
