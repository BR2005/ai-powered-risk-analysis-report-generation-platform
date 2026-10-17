"""
Shared Assessment State – the single source of truth passed between all
agents in the autonomous multi-agent workflow.

This replaces the ad-hoc dict returned by the old AgentWorkflowOrchestrator
and makes every piece of state explicit and type-safe.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.engine.scanner import ScanFinding


@dataclass
class AgentExecutionRecord:
    """One entry in the execution log, written after each agent completes."""

    agent_name: str
    started_at: str
    completed_at: str
    duration_seconds: float
    supervisor_decision: dict[str, Any]  # what Gemma 4 / fallback decided
    output_summary: str  # short human-readable description of output

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": round(self.duration_seconds, 3),
            "supervisor_decision": self.supervisor_decision,
            "output_summary": self.output_summary,
        }


@dataclass
class SharedAssessmentState:
    """Mutable state container shared across all agents during one assessment run."""

    # ── Inputs (set before the workflow starts) ──────────────────────────────
    project_name: str = ""
    architecture_text: str | None = None
    workspace_dir: Path | None = None
    target_frameworks: list[str] = field(default_factory=list)

    # ── Agent outputs (populated as agents complete) ──────────────────────────
    recon_summary: dict[str, Any] = field(default_factory=dict)
    findings: list[ScanFinding] = field(default_factory=list)
    risk_result: dict[str, Any] | None = None
    compliance_result: dict[str, Any] | None = None
    remediation_roadmap: list[dict[str, Any]] = field(default_factory=list)
    final_report: dict[str, Any] | None = None

    # ── Workflow tracking ─────────────────────────────────────────────────────
    completed_agents: set[str] = field(default_factory=set)
    execution_log: list[AgentExecutionRecord] = field(default_factory=list)
    supervisor_iterations: int = 0
    extra_security_loops: int = 0

    def log_execution(
        self,
        agent_name: str,
        started_at: datetime,
        supervisor_decision: dict[str, Any],
        output_summary: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        record = AgentExecutionRecord(
            agent_name=agent_name,
            started_at=started_at.isoformat(),
            completed_at=now.isoformat(),
            duration_seconds=(now - started_at).total_seconds(),
            supervisor_decision=supervisor_decision,
            output_summary=output_summary,
        )
        self.execution_log.append(record)
        self.completed_agents.add(agent_name)

    def to_pipeline_result(self) -> dict[str, Any]:
        """Convert state into the dict shape the existing API layer expects."""
        return {
            "recon_summary": self.recon_summary,
            "findings": self.findings,
            "risk_result": self.risk_result or {
                "overall_risk_score": 0.0,
                "risk_level": "INFORMATIONAL",
                "severity_breakdown": {},
                "risk_narrative": "No findings detected.",
            },
            "compliance_result": self.compliance_result or {
                "control_mappings": [],
                "compliance_score": 0.0,
                "compliance_breakdown": {},
                "framework_coverage": {},
            },
            "remediation_roadmap": self.remediation_roadmap,
            "agent_execution_log": [r.to_dict() for r in self.execution_log],
            "supervisor_iterations": self.supervisor_iterations,
        }
