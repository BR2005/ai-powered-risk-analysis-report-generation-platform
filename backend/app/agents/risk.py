from typing import Any
from app.engine.scanner import ScanFinding
from app.engine.scoring import ScoringEngine

class RiskAssessmentAgent:
    """Agent 4: Calculates authoritative deterministic risk scores, severity breakdown, and risk category levels."""

    def __init__(self):
        self.engine = ScoringEngine()

    async def execute(self, findings: list[ScanFinding]) -> dict[str, Any]:
        risk_score, risk_level, severity_breakdown = self.engine.calculate_risk(findings)

        # Build transparent calculation explanation
        critical_count = severity_breakdown.get("CRITICAL", 0)
        high_count = severity_breakdown.get("HIGH", 0)
        medium_count = severity_breakdown.get("MEDIUM", 0)
        low_count = severity_breakdown.get("LOW", 0)

        risk_narrative = (
            f"Overall Risk Score is {risk_score}/100 ({risk_level}). "
            f"Evaluated {len(findings)} finding(s): {critical_count} Critical, {high_count} High, "
            f"{medium_count} Medium, {low_count} Low. "
        )
        if critical_count > 0:
            risk_narrative += "Presence of Critical vulnerabilities directly escalates system risk level to CRITICAL."
        elif high_count > 0:
            risk_narrative += "Presence of High severity vulnerabilities establishes HIGH risk threshold."
        else:
            risk_narrative += "No Critical or High vulnerabilities detected in evaluated attack surfaces."

        return {
            "overall_risk_score": risk_score,
            "risk_level": risk_level,
            "severity_breakdown": severity_breakdown,
            "risk_narrative": risk_narrative
        }
