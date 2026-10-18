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
from app.engine.scanner import ScanFinding

logger = logging.getLogger(__name__)

# ─── Tool execution allowlist (maps agent name → callable) ────────────────────
# Only agents listed here may ever be dispatched. Any model output routing to
# a name not in this map is safely rejected, preventing arbitrary code execution.
ALLOWED_AGENT_TOOLS: set[str] = {
    "recon",
    "security",
    "evidence",
    "risk",
    "compliance",
    "remediation",
    "report",
}


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
        assessment_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the full autonomous multi-agent assessment pipeline.
        Returns the same dict shape as the old orchestrator, PLUS
        'agent_execution_log' and 'supervisor_iterations' fields.
        """
        state = SharedAssessmentState(
            project_name=project_name,
            assessment_id=assessment_id,
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
                missing_required_agents = [
                    agent
                    for agent in ("recon", "security", "risk", "report")
                    if agent not in state.completed_agents
                ]
                if missing_required_agents:
                    if state.supervisor_iterations >= MAX_SUPERVISOR_ITERATIONS:
                        raise RuntimeError(
                            "Supervisor reached the iteration limit before required "
                            f"agents completed: {', '.join(missing_required_agents)}."
                        )
                    next_agent = missing_required_agents[0]
                    decision.next_agent = next_agent
                    decision.reason = (
                        "FINISH was deferred because required agents had not completed; "
                        f"running {next_agent}."
                    )
                    logger.warning(
                        "Deferring FINISH; required agent(s) still pending: %s",
                        ", ".join(missing_required_agents),
                    )
                else:
                    state.execution_log.append(
                        _make_finish_record(decision.to_dict(), state.supervisor_iterations)
                    )
                    break

            if (
                state.supervisor_iterations >= MAX_SUPERVISOR_ITERATIONS
                and next_agent != "FINISH"
            ):
                raise RuntimeError(
                    "Supervisor iteration limit reached before the pipeline could finish."
                )

            # ── Safety Allowlist Enforcement ─────────────────────────────────
            if next_agent not in ALLOWED_AGENT_TOOLS:
                raise RuntimeError(
                    f"Supervisor attempted to dispatch unapproved agent '{next_agent}'."
                )

            # ── Dispatch to the selected agent ────────────────────────────────
            started_at = datetime.now(timezone.utc)
            output_summary = await self._dispatch(next_agent, state)

            # Track extra security loops for bounded feedback loop
            if next_agent in ("security", "evidence") and next_agent in state.completed_agents:
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

        else:
            raise RuntimeError(
                "Supervisor iteration limit reached before the pipeline could finish."
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
            existing_keys = {_finding_key(finding) for finding in state.findings}
            for f in raw_findings:
                key = _finding_key(f)
                if key not in existing_keys:
                    state.findings.append(f)
                    existing_keys.add(key)
            return f"Security scan complete: {len(raw_findings)} raw finding(s) detected."

        elif agent_name == "evidence":
            validated_findings = await self.evidence_agent.execute(
                findings=state.findings,
                workspace_dir=state.workspace_dir,
            )
            existing_indices = {
                _finding_key(finding): index
                for index, finding in enumerate(state.findings)
            }
            for finding in validated_findings:
                key = _finding_key(finding)
                existing_index = existing_indices.get(key)
                if existing_index is None:
                    existing_indices[key] = len(state.findings)
                    state.findings.append(finding)
                else:
                    state.findings[existing_index] = finding
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
                "id": state.assessment_id or "N/A",
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


def _finding_key(finding: ScanFinding) -> str:
    return f"{finding.file_path}:{finding.line_start}:{finding.category}:{finding.title}"


# ─── Module-level singleton (replaces old orchestrator singleton) ──────────────
multi_agent_orchestrator = MultiAgentOrchestrator()


if __name__ == "__main__":
    import asyncio

    async def main():
        print("=" * 75)
        print("  Gemma 4 Autonomous Multi-Agent Security & Compliance Assessment")
        print("=" * 75)

        sample_workspace = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "sample-projects"
            / "insecure-rag-agent"
        )
        target_dir = sample_workspace if sample_workspace.exists() else None

        print(f"Target Project   : Insecure RAG Agent Demo")
        print(f"Target Directory : {target_dir or 'Architecture Specification'}")
        print("Initiating autonomous supervisor loop...\n")

        results = await multi_agent_orchestrator.run_pipeline(
            project_name="Terminal Live Assessment Demo",
            architecture_text="System connects to ChromaDB vector store and executes untrusted Python LLM tools.",
            workspace_dir=target_dir,
            target_frameworks=["OWASP-GENAI", "NIST-AI-RMF", "EU-AI-ACT"],
        )

        print("\n" + "=" * 75)
        print("  Autonomous Multi-Agent Collaboration Trace")
        print("=" * 75)
        for idx, entry in enumerate(results.get("agent_execution_log", [])):
            agent = entry.get("agent_name", "")
            duration = entry.get("duration_seconds", 0.0)
            decision = entry.get("supervisor_decision", {})
            reason = decision.get("reason", "")
            source = decision.get("source", "gemma4")
            extra = " [FEEDBACK LOOP]" if decision.get("needs_extra_security_check") else ""
            print(f"[{idx + 1}] Agent: {agent.upper():<12} | Runtime: {duration:.2f}s | Source: {source}{extra}")
            print(f"    Supervisor Rationale: \"{reason}\"")
            print(f"    Output Summary      : {entry.get('output_summary', '')}\n")

        print("=" * 75)
        print("  Assessment Audit Results")
        print("=" * 75)
        risk = results.get("risk_result", {})
        comp = results.get("compliance_result", {})
        print(f"Findings Detected  : {len(results.get('findings', []))}")
        print(f"Risk Score         : {risk.get('overall_risk_score', 0)}/100 ({risk.get('risk_level', 'UNKNOWN')})")
        print(f"Compliance Score   : {comp.get('compliance_score', 0):.1f}%")
        print(f"Supervisor Total   : {results.get('supervisor_iterations', 0)} iterations")
        print(f"Remediation Steps  : {len(results.get('remediation_roadmap', []))}")
        print("=" * 75)
    asyncio.run(main())
    asyncio.run(main())
