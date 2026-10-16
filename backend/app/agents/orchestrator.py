from pathlib import Path
from typing import Any
from app.agents.reconnaissance import ReconnaissanceAgent
from app.agents.security import SecurityAnalysisAgent
from app.agents.evidence import EvidenceValidationAgent
from app.agents.risk import RiskAssessmentAgent
from app.agents.compliance import ComplianceMappingAgent
from app.agents.remediation import RemediationAgent
from app.agents.reporter import ReportGenerationAgent

class AgentWorkflowOrchestrator:
    """Coordinates the 7 specialized assessment agents in a sequential, evidence-grounded pipeline."""

    def __init__(self):
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
        target_frameworks: list[str]
    ) -> dict[str, Any]:
        # Stage 1: Reconnaissance
        recon_result = await self.recon_agent.execute(
            architecture_text=architecture_text,
            workspace_dir=workspace_dir
        )

        # Stage 2: Security Analysis
        raw_findings = await self.security_agent.execute(workspace_dir=workspace_dir)

        # Stage 3: Evidence Validation
        validated_findings = await self.evidence_agent.execute(
            findings=raw_findings,
            workspace_dir=workspace_dir
        )

        # Stage 4: Risk Assessment
        risk_result = await self.risk_agent.execute(findings=validated_findings)

        # Stage 5: Compliance Mapping
        compliance_result = await self.compliance_agent.execute(
            findings=validated_findings,
            target_frameworks=target_frameworks,
            recon_summary=recon_result
        )

        # Stage 6: Remediation Recommendations
        remediation_roadmap = await self.remediation_agent.execute(
            findings=validated_findings,
            control_mappings=compliance_result["control_mappings"]
        )

        # Package state into full assessment result
        return {
            "recon_summary": recon_result,
            "findings": validated_findings,
            "risk_result": risk_result,
            "compliance_result": compliance_result,
            "remediation_roadmap": remediation_roadmap,
        }

orchestrator = AgentWorkflowOrchestrator()
