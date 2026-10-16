from typing import Any
from app.engine.scanner import ScanFinding
from app.engine.compliance import ComplianceMapper
from app.engine.scoring import ScoringEngine

class ComplianceMappingAgent:
    """Agent 5: Maps findings to crosswalk frameworks and computes compliance posture."""

    def __init__(self):
        self.mapper = ComplianceMapper()
        self.scoring = ScoringEngine()

    async def execute(
        self,
        findings: list[ScanFinding],
        target_frameworks: list[str],
        recon_summary: dict | None = None
    ) -> dict[str, Any]:
        # 1. Evaluate control statuses
        control_mappings = self.mapper.evaluate_controls(
            findings=findings,
            target_frameworks=target_frameworks,
            recon_summary=recon_summary
        )

        # 2. Calculate compliance score & breakdown
        compliance_score, compliance_breakdown = self.scoring.calculate_compliance(control_mappings)

        # Group stats by framework
        framework_coverage: dict[str, dict[str, int]] = {}
        for cm in control_mappings:
            fid = cm["framework_id"]
            st = cm["status"]
            if fid not in framework_coverage:
                framework_coverage[fid] = {
                    "total": 0,
                    "IMPLEMENTED_WITH_EVIDENCE": 0,
                    "PARTIALLY_IMPLEMENTED": 0,
                    "MISSING_WITH_EVIDENCE": 0,
                    "NOT_EVIDENCED": 0,
                    "NOT_APPLICABLE": 0,
                }
            framework_coverage[fid]["total"] += 1
            if st in framework_coverage[fid]:
                framework_coverage[fid][st] += 1

        return {
            "control_mappings": control_mappings,
            "compliance_score": compliance_score,
            "compliance_breakdown": compliance_breakdown,
            "framework_coverage": framework_coverage
        }
