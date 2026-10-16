"""
Multi-Agent Orchestrator with Gemma 4 Supervision.

Replaces the old fixed-sequence AgentWorkflowOrchestrator with an
autonomous workflow graph:

  ┌─────────────────────────────────────────────────────────────────┐
  │                     SUPERVISOR (Gemma 4)                        │
  │    Reads SharedAssessmentState → decides next_agent → routes    │
  └─────────────┬───────────────────────────────────────────────────┘
                │ conditional routing
      ┌─────────┼──────────────────────────────────────┐
      ▼         ▼         ▼         ▼         ▼        ▼
   recon   security  evidence   risk  compliance  remediation → report → FINISH

Conditional feedback loop:
  If Gemma 4 decides "security" or "evidence" after both already ran,
  an extra investigation loop is triggered (bounded by MAX_SUPERVISOR_ITERATIONS).

All existing agents are reused unchanged.  The orchestrator only adds the
supervisor layer and shared state tracking on top.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agents.reconnaissance import ReconnaissanceAgent
from app.agents.security import SecurityAnalysisAgent
from app.agents.evidence import EvidenceValidationAgent
from app.agents.risk import RiskAssessmentAgent
from app.agents.compliance import ComplianceMappingAgent
from app.agents.remediation import RemediationAgent
from app.agents.reporter import ReportGenerationAgent
from app.agents.supervisor import gemma4_supervisor, MAX_SUPERVISOR_ITERATIONS
from app.agents.state import SharedAssessmentState

logger = logging.getLogger(__name__)

# ─── Tool execution allowlist (maps agent name → callable) ────────────────────
# Only agents listed here may ever be dispatched.  Any model output routing to
# a name not in this map is silently dropped and the supervisor is called again.

_AGENT_REGISTRY: dict[str, Any] = {}  # populated after class definitions


class MultiAgentOrchestrator:
    """
    Autonomous multi-agent workflow orchestrated by the Gemma 4 Supervisor.

    Features:
    - Gemma 4 decides which agent runs next at every step
    - Shared state is passed between all agents
    - Conditional routing: supervisor can request additional security checks
    - Bounded feedback loop: at most MAX_SUPERVISOR_ITERATIONS supervisor calls
    - Full execution log persisted for UI display
    """

    def __init__(self) -> None:
        self.recon_agent = ReconnaissanceAgent()
        self.security_agent = SecurityAnalysisAgent()
        self.evidence_agent = EvidenceValidationAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.compliance_agent = ComplianceMappingAgent()
        self.remediation_agent = RemediationAgent()
        self.reporter_agent = ReportGenerationAgent()

    async def run_pipeline(
        self,
        project_name: str,
        architecture_text: str | None,
        workspace_dir: Path | None,
        target_frameworks: list[str],
    ) -> dict[str, Any]:
        """
        Run the full autonomous multi-agent assessment pipeline.
        Returns the same dict shape as the old orchestrator, PLUS
        'agent_execution_log' and 'supervisor_iterations' fields.
        """
        state = SharedAssessmentState(
            project_name=project_name,
            architecture_text=architecture_text,
            workspace_dir=workspace_dir,
            target_frameworks=target_frameworks,
        )

        logger.info("MultiAgentOrchestrator: starting assessment for '%s'", project_name)

        while state.supervisor_iterations < MAX_SUPERVISOR_ITERATIONS:
            state.supervisor_iterations += 1

            # ── Ask Gemma 4 supervisor for the next routing decision ──────────
            decision = await gemma4_supervisor.decide(state)
            next_agent = decision.next_agent

            logger.info(
                "[Iter %d] Supervisor→ %s | %s",
                state.supervisor_iterations,
                next_agent,
                decision.reason,
            )

            if next_agent == "FINISH":
                # Persist the FINISH decision in the log
                state.execution_log.append(
                    _make_finish_record(decision.to_dict(), state.supervisor_iterations)
                )
                break

            # ── Dispatch to the selected agent ────────────────────────────────
            started_at = datetime.now(timezone.utc)
            output_summary = await self._dispatch(next_agent, state)

            # Track extra security loops for the supervisor
            if next_agent in ("security", "evidence") and next_agent in (
                set(state.completed_agents) - {next_agent}
            ):
                state.extra_security_loops += 1

            # Record execution in shared state
            decision_dict = decision.to_dict()
            decision_dict["iteration"] = state.supervisor_iterations
            state.log_execution(
                agent_name=next_agent,
                started_at=started_at,
                supervisor_decision=decision_dict,
                output_summary=output_summary,
            )

        logger.info(
            "MultiAgentOrchestrator: assessment complete after %d supervisor iterations.",
            state.supervisor_iterations,
        )
        return state.to_pipeline_result()

    # ─── Agent dispatch router ─────────────────────────────────────────────

    async def _dispatch(self, agent_name: str, state: SharedAssessmentState) -> str:
        """Route control to the correct agent and update state. Returns output summary."""

        if agent_name == "recon":
            state.recon_summary = await self.recon_agent.execute(
                architecture_text=state.architecture_text,
                workspace_dir=state.workspace_dir,
            )
            return (
                f"Identified {len(state.recon_summary.get('components', []))} components, "
                f"{len(state.recon_summary.get('trust_boundaries', []))} trust boundaries."
            )

        elif agent_name == "security":
            raw_findings = await self.security_agent.execute(
                workspace_dir=state.workspace_dir
            )
            # Merge new findings (de-duplicate by key)
            existing_keys = {
                f"{f.file_path}:{f.line_start}:{f.category}:{f.title}"
                for f in state.findings
            }
            for f in raw_findings:
                key = f"{f.file_path}:{f.line_start}:{f.category}:{f.title}"
                if key not in existing_keys:
                    state.findings.append(f)
                    existing_keys.add(key)
            return f"Security scan complete: {len(raw_findings)} raw finding(s) detected."

        elif agent_name == "evidence":
            state.findings = await self.evidence_agent.execute(
                findings=state.findings,
                workspace_dir=state.workspace_dir,
            )
            verified = sum(
                1 for f in state.findings if f.validation_status == "VERIFIED"
            )
            return (
                f"Evidence validation complete: {verified}/{len(state.findings)} findings verified."
            )

        elif agent_name == "risk":
            state.risk_result = await self.risk_agent.execute(findings=state.findings)
            return (
                f"Risk score: {state.risk_result['overall_risk_score']}/100 "
                f"({state.risk_result['risk_level']})."
            )

        elif agent_name == "compliance":
            state.compliance_result = await self.compliance_agent.execute(
                findings=state.findings,
                target_frameworks=state.target_frameworks,
                recon_summary=state.recon_summary,
            )
            return (
                f"Compliance score: {state.compliance_result['compliance_score']:.1f}% "
                f"across {len(state.target_frameworks)} frameworks."
            )

        elif agent_name == "remediation":
            control_mappings = (
                state.compliance_result["control_mappings"]
                if state.compliance_result
                else []
            )
            state.remediation_roadmap = await self.remediation_agent.execute(
                findings=state.findings,
                control_mappings=control_mappings,
            )
            return f"Generated {len(state.remediation_roadmap)} remediation step(s)."

        elif agent_name == "report":
            assessment_summary_dict: dict[str, Any] = {
                "id": "N/A",
                "project_name": state.project_name,
            }
            control_mappings = (
                state.compliance_result["control_mappings"]
                if state.compliance_result
                else []
            )
            findings_dicts = [
                {
                    "finding_id": f.finding_id,
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity,
                    "remediation": f.remediation,
                    "file_path": f.file_path,
                }
                for f in state.findings
            ]
            state.final_report = await self.reporter_agent.execute(
                assessment_summary=assessment_summary_dict,
                recon_summary=state.recon_summary,
                findings=findings_dicts,
                control_mappings=control_mappings,
                remediation_roadmap=state.remediation_roadmap,
            )
            return "Final assessment report synthesized."

        else:
            logger.warning("Unknown agent dispatched: '%s' — skipping.", agent_name)
            return f"Unknown agent '{agent_name}' — skipped."


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_finish_record(decision_dict: dict[str, Any], iteration: int):
    """Create the FINISH execution log entry."""
    from app.agents.state import AgentExecutionRecord
    now = datetime.now(timezone.utc).isoformat()
    decision_dict["iteration"] = iteration
    return AgentExecutionRecord(
        agent_name="FINISH",
        started_at=now,
        completed_at=now,
        duration_seconds=0.0,
        supervisor_decision=decision_dict,
        output_summary="Supervisor terminated workflow.",
    )


# ─── Module-level singleton (replaces old orchestrator singleton) ──────────────
multi_agent_orchestrator = MultiAgentOrchestrator()
