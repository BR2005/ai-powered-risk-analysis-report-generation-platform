from typing import Any
from app.engine.scanner import ScanFinding
from app.agents.llm_provider import llm_provider

class RemediationAgent:
    """Agent 6: Produces prioritized, actionable remediation steps linked to detected evidence and controls."""

    async def execute(self, findings: list[ScanFinding], control_mappings: list[dict]) -> list[dict[str, Any]]:
        remediation_plan: list[dict[str, Any]] = []

        # Sort findings by severity (Critical first)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFORMATIONAL": 4}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity.upper(), 5))

        for idx, f in enumerate(sorted_findings, start=1):
            # Find linked controls
            linked_controls = [
                f"{cm['framework_id']}:{cm['control_id']} ({cm['control_title']})"
                for cm in control_mappings
                if cm["status"] in ("MISSING_WITH_EVIDENCE", "PARTIALLY_IMPLEMENTED")
                and (cm["control_id"] == f.owasp_id or cm.get("control_category") == f.category)
            ]

            plan_item = {
                "step_number": idx,
                "finding_id": f.finding_id,
                "title": f.title,
                "severity": f.severity,
                "target_file": f.file_path,
                "target_line": f.line_start,
                "remediation_summary": f.remediation or "Implement defensive guardrail and input sanitization.",
                "remediation_code_diff": f.remediation_snippet,
                "linked_compliance_controls": linked_controls[:3],
                "effort_estimate": "LOW" if f.severity in ("LOW", "INFORMATIONAL") else ("MEDIUM" if f.severity == "MEDIUM" else "HIGH")
            }
            remediation_plan.append(plan_item)

        return remediation_plan
