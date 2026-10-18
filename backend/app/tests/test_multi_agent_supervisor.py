import json
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path
import tempfile

from app.agents.state import SharedAssessmentState
from app.agents.supervisor import (
    Gemma4Supervisor,
    SupervisorDecision,
    ALLOWED_AGENTS,
    MAX_SUPERVISOR_ITERATIONS,
    MAX_EXTRA_SECURITY_LOOPS,
)
from app.agents.multi_agent_orchestrator import MultiAgentOrchestrator, ALLOWED_AGENT_TOOLS
from app.agents.supervisor import gemma4_supervisor
from app.engine.scanner import ScanFinding


@pytest.mark.asyncio
async def test_confirmed_finding_e2e_flow():
    """
    Test 1: Confirmed Finding Scenario
    Autonomous pipeline runs on real workspace with insecure code,
    detects finding, verifies evidence, and confirms finding in shared state.
    """
    orchestrator = MultiAgentOrchestrator()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        vulnerable_file = tmp_path / "rag_pipeline.py"
        vulnerable_file.write_text(
            """
import os
def answer_query(user_prompt):
    # Insecure direct eval and secret exposure
    api_key = "sk-live-1234567890abcdef1234567890abcdef"
    output = eval(user_prompt)
    return output
""",
            encoding="utf-8",
        )

        results = await orchestrator.run_pipeline(
            project_name="Confirmed Finding Test",
            architecture_text="System with RAG agent using LLM.",
            workspace_dir=tmp_path,
            target_frameworks=["OWASP-GENAI", "NIST-AI-RMF"],
        )

        # 1. Verify findings exist
        findings = results["findings"]
        assert len(findings) >= 1

        # 2. Verify evidence validation verified at least one finding
        verified_findings = [f for f in findings if f.validation_status == "VERIFIED"]
        assert len(verified_findings) >= 1
        assert verified_findings[0].numerical_score > 0

        # 3. Verify execution log recorded all steps
        exec_log = results["agent_execution_log"]
        assert len(exec_log) >= 5
        agent_names = [e["agent_name"] for e in exec_log]
        assert "recon" in agent_names
        assert "security" in agent_names
        assert "evidence" in agent_names
        assert "risk" in agent_names
        assert "FINISH" in agent_names

        # 4. Verify supervisor decisions are tracked
        for entry in exec_log:
            decision = entry["supervisor_decision"]
            assert "next_agent" in decision
            assert "reason" in decision
            assert "source" in decision


@pytest.mark.asyncio
async def test_additional_investigation_loop_scenario():
    """
    Test 2: Additional-Investigation Loop Scenario
    Gemma 4 model explicitly returns a routing decision to loop back to 'evidence'
    due to unverified findings, testing conditional routing and loop counting.
    """
    supervisor = Gemma4Supervisor()
    orchestrator = MultiAgentOrchestrator()

    # Sequence of decisions simulating Gemma 4 directing workflow with a loop:
    # 1. recon -> 2. security -> 3. evidence -> 4. loop back to evidence for deeper check -> 5. risk -> 6. compliance -> 7. remediation -> 8. report
    model_responses = [
        json.dumps({"next_agent": "recon", "reason": "Analyze architecture first.", "needs_extra_security_check": False}),
        json.dumps({"next_agent": "security", "reason": "Run AST scan.", "needs_extra_security_check": False}),
        json.dumps({"next_agent": "evidence", "reason": "Verify findings.", "needs_extra_security_check": False}),
        # Gemma 4 notices findings need extra verification loop:
        json.dumps({"next_agent": "evidence", "reason": "Critical findings require secondary evidence check.", "needs_extra_security_check": True}),
        json.dumps({"next_agent": "risk", "reason": "Score risks.", "needs_extra_security_check": False}),
        json.dumps({"next_agent": "compliance", "reason": "Map controls.", "needs_extra_security_check": False}),
        json.dumps({"next_agent": "remediation", "reason": "Generate roadmaps.", "needs_extra_security_check": False}),
        json.dumps({"next_agent": "report", "reason": "Synthesize report.", "needs_extra_security_check": False}),
        json.dumps({"next_agent": "FINISH", "reason": "All tasks completed.", "needs_extra_security_check": False}),
    ]

    response_iter = iter(model_responses)

    async def mock_generate_completion(*args, **kwargs):
        try:
            return next(response_iter)
        except StopIteration:
            return json.dumps({"next_agent": "FINISH", "reason": "Done", "needs_extra_security_check": False})

    with patch("app.agents.supervisor.llm_provider.generate_completion", side_effect=mock_generate_completion):
        results = await orchestrator.run_pipeline(
            project_name="Investigation Loop Test",
            architecture_text="Vector DB with API tool execution.",
            workspace_dir=None,
            target_frameworks=["OWASP-GENAI"],
        )

        exec_log = results["agent_execution_log"]
        evidence_runs = [e for e in exec_log if e["agent_name"] == "evidence"]
        
        # Verify evidence agent executed twice due to Gemma 4 routing decision
        assert len(evidence_runs) >= 2
        # Check that the second run has the extra security check reason
        assert evidence_runs[1]["supervisor_decision"]["needs_extra_security_check"] is True
        assert "secondary evidence check" in evidence_runs[1]["supervisor_decision"]["reason"]


@pytest.mark.asyncio
async def test_termination_scenario_iteration_limit():
    """
    Test 3: Termination Scenario
    When the supervisor hits MAX_SUPERVISOR_ITERATIONS, it must terminate gracefully
    with 'FINISH' and persist all state and logs.
    """
    supervisor = Gemma4Supervisor()
    
    # State already at MAX_SUPERVISOR_ITERATIONS
    state = SharedAssessmentState(
        project_name="Limit Test",
        supervisor_iterations=MAX_SUPERVISOR_ITERATIONS,
    )

    decision = await supervisor.decide(state)
    assert decision.next_agent == "FINISH"
    assert "limit" in decision.reason.lower()
    assert decision.source == "supervisor_guardrail"


@pytest.mark.asyncio
async def test_safety_allowlist_and_malformed_model_response():
    """
    Test 4: Safety & Model Validation
    - Disallowed agents in Gemma 4 responses are rejected.
    - Markdown-wrapped JSON is parsed correctly.
    - Malformed responses fallback safely to priority queue without arbitrary execution.
    """
    supervisor = Gemma4Supervisor()

    # 1. Allowlist rejection: model returns an arbitrary / disallowed command
    bad_model_raw = json.dumps({"next_agent": "system_rmdir", "reason": "hack", "needs_extra_security_check": False})
    decision = supervisor._parse_model_response(bad_model_raw)
    assert decision is None  # Must reject disallowed agent

    # 2. Markdown fence parsing: Gemma 4 wraps JSON in ```json ... ```
    fenced_raw = """```json
{
  "next_agent": "recon",
  "reason": "Map out GenAI pipeline architecture.",
  "needs_extra_security_check": false
}
```"""
    parsed = supervisor._parse_model_response(fenced_raw)
    assert parsed is not None
    assert parsed.next_agent == "recon"
    assert parsed.source == "gemma4"

    # 3. Tool allowlist check in orchestrator
    assert "system_rmdir" not in ALLOWED_AGENT_TOOLS
    assert "recon" in ALLOWED_AGENT_TOOLS
    assert "security" in ALLOWED_AGENT_TOOLS


@pytest.mark.asyncio
async def test_early_finish_is_replaced_with_required_agent_routes():
    orchestrator = MultiAgentOrchestrator()
    orchestrator._dispatch = AsyncMock(return_value="completed")

    with patch.object(
        gemma4_supervisor,
        "decide",
        new=AsyncMock(
            return_value=SupervisorDecision(
                "FINISH",
                "Stop before doing any work.",
            )
        ),
    ):
        results = await orchestrator.run_pipeline(
            project_name="Early Finish Guard Test",
            architecture_text=None,
            workspace_dir=None,
            target_frameworks=[],
        )

    executed_agents = {
        entry["agent_name"]
        for entry in results["agent_execution_log"]
        if entry["agent_name"] != "FINISH"
    }
    assert executed_agents == ALLOWED_AGENT_TOOLS
    assert results["agent_execution_log"][-1]["agent_name"] == "FINISH"
    assert results["supervisor_iterations"] <= MAX_SUPERVISOR_ITERATIONS


@pytest.mark.asyncio
async def test_early_report_is_rejected_and_duplicate_report_finishes():
    orchestrator = MultiAgentOrchestrator()
    orchestrator._dispatch = AsyncMock(return_value="completed")

    with patch.object(
        gemma4_supervisor,
        "decide",
        new=AsyncMock(
            return_value=SupervisorDecision(
                "report",
                "Generate the report before the analysis is complete.",
            )
        ),
    ):
        results = await orchestrator.run_pipeline(
            project_name="Early Report Guard Test",
            architecture_text=None,
            workspace_dir=None,
            target_frameworks=[],
        )

    agent_order = [
        entry["agent_name"] for entry in results["agent_execution_log"]
    ]
    assert agent_order.index("report") > agent_order.index("remediation")
    assert agent_order[-1] == "FINISH"
    assert results["supervisor_iterations"] <= MAX_SUPERVISOR_ITERATIONS
