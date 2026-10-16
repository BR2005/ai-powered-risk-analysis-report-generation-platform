from dataclasses import dataclass
from app.engine.scanner import ScanFinding

SEVERITY_WEIGHTS = {
    "CRITICAL": 10.0,
    "HIGH": 7.5,
    "MEDIUM": 5.0,
    "LOW": 2.5,
    "INFORMATIONAL": 0.5,
}

CONFIDENCE_MULTIPLIERS = {
    "CONFIRMED": 1.0,
    "SUSPECTED": 0.75,
    "INFORMATIONAL": 0.5,
    "NOT_VERIFIED": 0.3,
}

@dataclass
class ScoreResult:
    overall_risk_score: float # 0.0 - 100.0
    risk_level: str           # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
    compliance_score: float   # 0.0 - 100.0
    severity_breakdown: dict[str, int]
    compliance_breakdown: dict[str, int]

class ScoringEngine:
    """Calculates deterministic, transparent risk scores and compliance coverage percentages."""

    def calculate_risk(self, findings: list[ScanFinding]) -> tuple[float, str, dict[str, int]]:
        severity_breakdown = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFORMATIONAL": 0,
        }

        if not findings:
            return 0.0, "INFORMATIONAL", severity_breakdown

        weighted_sum = 0.0
        for f in findings:
            sev = f.severity.upper()
            if sev in severity_breakdown:
                severity_breakdown[sev] += 1
            weight = SEVERITY_WEIGHTS.get(sev, 2.5)
            conf_mult = CONFIDENCE_MULTIPLIERS.get(f.confidence.upper(), 0.75)
            # Factor in finding's numerical score (0-10) scaled by confidence
            finding_impact = (f.numerical_score / 10.0) * weight * conf_mult
            weighted_sum += finding_impact

        # Normalize score into 0 - 100 range with non-linear saturation curve
        # High count of criticals saturates to 100
        # If any confirmed CRITICAL finding exists, base score is at least 75
        has_critical = severity_breakdown["CRITICAL"] > 0
        has_high = severity_breakdown["HIGH"] > 0

        raw_score = min(100.0, weighted_sum * 3.5)
        if has_critical:
            raw_score = max(75.0, raw_score)
        elif has_high:
            raw_score = max(50.0, raw_score)

        score = round(raw_score, 1)

        # Categorize overall risk level
        if score >= 75.0 or severity_breakdown["CRITICAL"] > 0:
            level = "CRITICAL"
        elif score >= 50.0 or severity_breakdown["HIGH"] > 0:
            level = "HIGH"
        elif score >= 25.0:
            level = "MEDIUM"
        elif score > 0.0:
            level = "LOW"
        else:
            level = "INFORMATIONAL"

        return score, level, severity_breakdown

    def calculate_compliance(self, control_mappings: list[dict]) -> tuple[float, dict[str, int]]:
        breakdown = {
            "IMPLEMENTED_WITH_EVIDENCE": 0,
            "PARTIALLY_IMPLEMENTED": 0,
            "MISSING_WITH_EVIDENCE": 0,
            "NOT_EVIDENCED": 0,
            "NOT_APPLICABLE": 0,
        }

        if not control_mappings:
            return 0.0, breakdown

        applicable_count = 0
        satisfied_weight = 0.0

        for cm in control_mappings:
            status = cm.get("status", "NOT_EVIDENCED")
            if status in breakdown:
                breakdown[status] += 1

            if status != "NOT_APPLICABLE":
                applicable_count += 1
                if status == "IMPLEMENTED_WITH_EVIDENCE":
                    satisfied_weight += 1.0
                elif status == "PARTIALLY_IMPLEMENTED":
                    satisfied_weight += 0.5
                elif status == "NOT_EVIDENCED":
                    # Absence of evidence is neutral, not awarded full compliance
                    satisfied_weight += 0.15
                elif status == "MISSING_WITH_EVIDENCE":
                    satisfied_weight += 0.0

        if applicable_count == 0:
            compliance_score = 100.0
        else:
            compliance_score = round((satisfied_weight / applicable_count) * 100.0, 1)

        return compliance_score, breakdown
