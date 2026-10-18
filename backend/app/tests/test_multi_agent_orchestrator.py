from types import SimpleNamespace

import pytest

from app.agents import multi_agent_orchestrator as orchestrator_module
from app.agents.multi_agent_orchestrator import MultiAgentOrchestrator
from app.agents.state import SharedAssessmentState
from app.agents.supervisor import SupervisorDecision
from app.engine.scanner import ScanFinding


def _finding(
    finding_id: str,
    title: str,
    validation_status: str = "REQUIRES_MANUAL_REVIEW",
) -> ScanFinding:
    return ScanFinding(
        finding_id=finding_id,
        title=title,
        description="Finding description",
        category="TEST_CATEGORY",
        severity="HIGH",
        numerical_score=8.0,
        confidence="SUSPECTED",
        validation_status=validation_status,
        owasp_id="LLM01",
        file_path="src/example.py",
        line_start=10,
    )


@pytest.mark.asyncio
async def test_premature_finish_runs_required_agents_and_report_uses_assessment_id(
    monkeypatch,
):
    orchestrator = MultiAgentOrchestrator()
    report_summaries = []

    async def decide(_state):
        return SupervisorDecision("FINISH", "Done", False)

    async def recon_execute(**_kwargs):
        return {"components": [], "trust_boundaries": []}

    async def security_execute(**_kwargs):
        return []

    async def risk_execute(**_kwargs):
        return {"overall_risk_score": 0, "risk_level": "INFORMATIONAL"}

    async def report_execute(**kwargs):
        report_summaries.append(kwargs["assessment_summary"])
        return {}

    monkeypatch.setattr(orchestrator_module.gemma4_supervisor, "decide", decide)
    orchestrator.recon_agent = SimpleNamespace(execute=recon_execute)
    orchestrator.security_agent = SimpleNamespace(execute=security_execute)
    orchestrator.risk_agent = SimpleNamespace(execute=risk_execute)
    orchestrator.reporter_agent = SimpleNamespace(execute=report_execute)

    result = await orchestrator.run_pipeline(
        project_name="Test project",
        architecture_text=None,
        workspace_dir=None,
        target_frameworks=[],
        assessment_id="assessment-123",
    )

    assert report_summaries[0]["id"] == "assessment-123"
    assert [
        entry["agent_name"] for entry in result["agent_execution_log"]
    ] == ["recon", "security", "risk", "report", "FINISH"]


@pytest.mark.asyncio
async def test_repeated_security_dispatch_increments_extra_loop_counter(monkeypatch):
    orchestrator = MultiAgentOrchestrator()
    decisions = iter(["security", "security", "recon", "risk", "report", "FINISH"])
    decision_count = 0

    async def decide(state):
        nonlocal decision_count
        decision_count += 1
        if decision_count == 3:
            assert state.extra_security_loops == 1
        return SupervisorDecision(next(decisions), "Test route", False)

    async def recon_execute(**_kwargs):
        return {"components": [], "trust_boundaries": []}

    async def security_execute(**_kwargs):
        return []

    async def risk_execute(**_kwargs):
        return {"overall_risk_score": 0, "risk_level": "INFORMATIONAL"}

    async def report_execute(**_kwargs):
        return {}

    monkeypatch.setattr(orchestrator_module.gemma4_supervisor, "decide", decide)
    orchestrator.recon_agent = SimpleNamespace(execute=recon_execute)
    orchestrator.security_agent = SimpleNamespace(execute=security_execute)
    orchestrator.risk_agent = SimpleNamespace(execute=risk_execute)
    orchestrator.reporter_agent = SimpleNamespace(execute=report_execute)

    await orchestrator.run_pipeline("Test project", None, None, [])


@pytest.mark.asyncio
async def test_evidence_validation_updates_findings_without_dropping_existing_findings():
    orchestrator = MultiAgentOrchestrator()
    original = _finding("F-1", "Security finding")
    other = _finding("F-2", "Previously merged finding")
    validated = _finding("F-1", "Security finding", "VERIFIED")
    state = SharedAssessmentState(findings=[original, other])

    async def validate(**_kwargs):
        return [validated]

    orchestrator.evidence_agent = SimpleNamespace(execute=validate)

    await orchestrator._dispatch("evidence", state)

    assert state.findings == [validated, other]
    assert state.findings[0].validation_status == "VERIFIED"


@pytest.mark.asyncio
async def test_non_finish_decision_at_iteration_limit_raises(monkeypatch):
    orchestrator = MultiAgentOrchestrator()

    async def decide(_state):
        return SupervisorDecision("recon", "Continue", False)

    monkeypatch.setattr(orchestrator_module, "MAX_SUPERVISOR_ITERATIONS", 1)
    monkeypatch.setattr(orchestrator_module.gemma4_supervisor, "decide", decide)

    with pytest.raises(RuntimeError, match="iteration limit"):
        await orchestrator.run_pipeline("Test project", None, None, [])
