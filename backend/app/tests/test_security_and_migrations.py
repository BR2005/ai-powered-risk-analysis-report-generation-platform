from sqlalchemy import create_engine, inspect, text
import httpx
import pytest

from app.config import settings
from app.database import ensure_assessment_tracking_columns


def test_assessment_and_findings_routes_require_api_key(client):
    assert client.get("/api/v1/assessments").status_code == 200

    response = client.get(
        "/api/v1/assessments",
        headers={"X-API-Key": "incorrect-key"},
    )
    assert response.status_code == 401

    response = client.get(
        "/api/v1/findings",
        headers={"X-API-Key": "incorrect-key"},
    )
    assert response.status_code == 401

    response = client.get(
        "/api/v1/assessments/unknown/report.pdf",
        headers={"X-API-Key": "incorrect-key"},
    )
    assert response.status_code == 401


def test_protected_routes_fail_closed_without_configured_key(client):
    settings.api_access_key = None
    response = client.get(
        "/api/v1/assessments",
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 503


def test_assessment_tracking_migration_is_portable_and_idempotent():
    migration_engine = create_engine("sqlite:///:memory:")
    try:
        with migration_engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE assessments (id VARCHAR(36) PRIMARY KEY)")
            )

        ensure_assessment_tracking_columns(migration_engine)
        ensure_assessment_tracking_columns(migration_engine)

        columns = {
            column["name"]
            for column in inspect(migration_engine).get_columns("assessments")
        }
        assert "agent_execution_log" in columns
        assert "supervisor_iterations" in columns
    finally:
        migration_engine.dispose()


@pytest.mark.asyncio
async def test_llm_provider_errors_do_not_log_api_keys(caplog):
    from unittest.mock import AsyncMock, patch

    from app.agents.llm_provider import LLMProvider

    api_key = "test-gemma-secret-key"
    original_api_key = settings.gemma_api_key
    settings.gemma_api_key = api_key

    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            return False

        async def post(self, url, **kwargs):
            raise httpx.ConnectError(f"request failed for {url}?key={api_key}")

    provider = LLMProvider()
    provider.provider = "gemma-4"
    provider._call_ollama = AsyncMock(return_value=None)
    try:
        with patch(
            "app.agents.llm_provider.httpx.AsyncClient",
            return_value=FailingClient(),
        ):
            await provider.generate_completion("system", "assessment data")
    finally:
        settings.gemma_api_key = original_api_key

    assert api_key not in caplog.text
