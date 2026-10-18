"""
Gemma 4 Supervisor – autonomous multi-agent routing brain.

The supervisor receives a SharedAssessmentState snapshot after each agent
completes and calls Gemma 4 to decide which agent (if any) should run next.
It never hardcodes a fixed sequence; every routing decision is produced by
the model and validated against a safe allowlist before execution.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.agents.llm_provider import llm_provider

logger = logging.getLogger(__name__)

# ─── Allowlist of agent names the supervisor may dispatch ────────────────────
ALLOWED_AGENTS: set[str] = {
    "recon",
    "security",
    "evidence",
    "risk",
    "compliance",
    "remediation",
    "report",
    "FINISH",
}

# Hard cap on how many times the supervisor may loop back
MAX_SUPERVISOR_ITERATIONS = 8

SYSTEM_PROMPT = """You are the Gemma 4 Multi-Agent Security Supervisor for an AI-Powered GenAI Security
Risk & Compliance Assessment Platform.

Your role is to decide which specialist agent should run NEXT based on the
current assessment state. You receive a JSON snapshot of the state and you
must return a JSON routing decision.

Available agents (only choose from this exact list):
  - "recon"       – Reconnaissance & architecture mapping
  - "security"    – Static security scanning & vulnerability detection
  - "evidence"    – Evidence verification & confidence classification
  - "risk"        – Risk scoring & severity calculation
  - "compliance"  – Compliance framework control mapping
  - "remediation" – Remediation recommendations generation
  - "report"      – Final report synthesis
  - "FINISH"      – Terminate assessment (all critical work done)

Rules you MUST follow:
1. Return ONLY valid JSON. No markdown fences, no extra text.
2. The JSON must have exactly three keys:
   {
     "next_agent": "<one of the 8 options above>",
     "reason": "<one sentence explaining why>",
     "needs_extra_security_check": <true | false>
   }
3. If there are CRITICAL or HIGH findings that have NOT been evidence-verified,
   route back to "evidence" or "security" for a deeper check.
4. If compliance has not been run but findings exist, route to "compliance".
5. Route to "FINISH" only when the report is ready OR the iteration limit is
   reached.
6. Never route to an agent that is already listed in completed_agents if it
   would be pure repetition with no new data.
"""


class SupervisorDecision:
    """Parsed and validated routing decision from Gemma 4."""

    def __init__(self, next_agent: str, reason: str, needs_extra_check: bool):
        self.next_agent = next_agent
        self.reason = reason
        self.needs_extra_check = needs_extra_check

    def to_dict(self) -> dict[str, Any]:
        return {
            "next_agent": self.next_agent,
            "reason": self.reason,
            "needs_extra_security_check": self.needs_extra_check,
        }


class Gemma4Supervisor:
    """
    Uses the actual Gemma 4 model to route agent execution.

    If Gemma 4 is unavailable (no key, Ollama offline) the supervisor
    falls back to a deterministic priority-queue so the platform stays
    functional.  All decisions—model-generated or fallback—are logged in
    the shared state with a 'source' field so the UI can distinguish them.
    """

    async def decide(
        self,
        state: "SharedAssessmentState",  # type: ignore[name-defined]
    ) -> SupervisorDecision:
        """
        Ask Gemma 4 which agent should run next and return a validated decision.
        """
        if state.supervisor_iterations >= MAX_SUPERVISOR_ITERATIONS:
            logger.warning(
                "Supervisor reached iteration limit (%d). Terminating.",
                MAX_SUPERVISOR_ITERATIONS,
            )
            return SupervisorDecision(
                next_agent="FINISH",
                reason=f"Investigation limit of {MAX_SUPERVISOR_ITERATIONS} iterations reached.",
                needs_extra_check=False,
            )

        # Build a compact state snapshot for the model
        state_snapshot = self._build_snapshot(state)
        user_prompt = f"Assessment state:\n{json.dumps(state_snapshot, indent=2)}\n\nDecide next agent."

        raw_response = await llm_provider.generate_completion(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        if raw_response:
            decision = self._parse_model_response(raw_response)
            if decision:
                decision_dict = decision.to_dict()
                decision_dict["source"] = "gemma4"
                logger.info(
                    "Gemma 4 routing decision (iter %d): %s — %s",
                    state.supervisor_iterations,
                    decision.next_agent,
                    decision.reason,
                )
                return decision

        # ── Deterministic fallback (Gemma 4 offline) ────────────────────────
        return self._fallback_decision(state)

    # ─── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _build_snapshot(state: "SharedAssessmentState") -> dict[str, Any]:  # type: ignore[name-defined]
        critical_count = sum(
            1 for f in state.findings if getattr(f, "severity", "") == "CRITICAL"
        )
        high_count = sum(
            1 for f in state.findings if getattr(f, "severity", "") == "HIGH"
        )
        unverified_count = sum(
            1
            for f in state.findings
            if getattr(f, "validation_status", "") == "REQUIRES_MANUAL_REVIEW"
        )
        return {
            "completed_agents": list(state.completed_agents),
            "findings_count": len(state.findings),
            "critical_findings": critical_count,
            "high_findings": high_count,
            "unverified_findings": unverified_count,
            "risk_scored": state.risk_result is not None,
            "compliance_done": state.compliance_result is not None,
            "remediation_done": bool(state.remediation_roadmap),
            "report_ready": state.final_report is not None,
            "extra_security_loops": state.extra_security_loops,
            "supervisor_iterations": state.supervisor_iterations,
        }

    @staticmethod
    def _parse_model_response(raw: str) -> SupervisorDecision | None:
        """
        Extract JSON from model response. Accepts both bare JSON and
        JSON wrapped in markdown code fences.
        """
        # Strip markdown fences if present
        stripped = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
        # Try to locate the first JSON object
        match = re.search(r"\{.*?\}", stripped, flags=re.DOTALL)
        if not match:
            logger.warning("Supervisor: no JSON object found in model response.")
            return None

        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            logger.warning("Supervisor: JSON parse error: %s", exc)
            return None

        next_agent = data.get("next_agent", "").strip()
        reason = data.get("reason", "Model routing decision.").strip()
        needs_extra = bool(data.get("needs_extra_security_check", False))

        # Safety: enforce allowlist
        if next_agent not in ALLOWED_AGENTS:
            logger.warning(
                "Supervisor: model returned disallowed agent '%s'. Falling back.",
                next_agent,
            )
            return None

        return SupervisorDecision(
            next_agent=next_agent,
            reason=reason,
            needs_extra_check=needs_extra,
        )

    @staticmethod
    def _fallback_decision(state: "SharedAssessmentState") -> SupervisorDecision:  # type: ignore[name-defined]
        """Priority-queue fallback used when Gemma 4 is offline."""
        done = state.completed_agents

        priority_queue = [
            ("recon", "Reconnaissance must run first to map the architecture."),
            ("security", "Security scan required to identify vulnerabilities."),
            ("evidence", "Evidence verification needed to validate findings."),
            ("risk", "Risk scoring required before compliance mapping."),
            ("compliance", "Compliance mapping needed to assess control coverage."),
            ("remediation", "Remediation recommendations required for report."),
            ("report", "All prerequisites complete — generating final report."),
        ]

        # Allow one extra security loop if there are high-severity findings
        if (
            "security" in done
            and "evidence" in done
            and state.extra_security_loops == 0
        ):
            critical_count = sum(
                1 for f in state.findings if getattr(f, "severity", "") == "CRITICAL"
            )
            if critical_count > 0 and "risk" not in done:
                return SupervisorDecision(
                    next_agent="risk",
                    reason="(fallback) Critical findings found — proceeding to risk scoring.",
                    needs_extra_check=False,
                )

        for agent_name, reason in priority_queue:
            if agent_name not in done:
                return SupervisorDecision(
                    next_agent=agent_name,
                    reason=f"(fallback) {reason}",
                    needs_extra_check=False,
                )

        return SupervisorDecision(
            next_agent="FINISH",
            reason="(fallback) All required agents have completed their work.",
            needs_extra_check=False,
        )


# Module-level singleton
gemma4_supervisor = Gemma4Supervisor()
