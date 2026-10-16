from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Any

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    database: str
    engine: str

class ControlSchema(BaseModel):
    control_id: str
    title: str
    category: str
    description: str
    reference_url: str | None = None
    verification_guidance: str | None = None
    is_conceptual_mapping: bool = False

class FrameworkSchema(BaseModel):
    id: str
    name: str
    version: str
    publisher: str
    category: str
    controls_count: int
    source_url: str
    disclaimer: str
    controls: list[ControlSchema] = []

class FrameworkListResponse(BaseModel):
    frameworks: list[FrameworkSchema]
    total_frameworks: int
    total_controls: int

class AssessmentCreateRequest(BaseModel):
    project_name: str = Field(..., min_length=2, max_length=150)
    description: str | None = None
    architecture_text: str | None = None
    target_frameworks: list[str] = Field(
        default=["OWASP-GENAI", "NIST-AI-RMF", "MITRE-ATLAS", "ISO-42001", "ISO-23894", "EU-AI-ACT"]
    )

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    code_snippet: str | None = None
    context_note: str | None = None
    is_redacted: bool = True

class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    assessment_id: str
    finding_id: str
    title: str
    description: str
    category: str
    severity: str
    numerical_score: float
    confidence: str
    validation_status: str
    owasp_id: str | None = None
    remediation: str | None = None
    remediation_snippet: str | None = None
    created_at: datetime
    evidences: list[EvidenceResponse] = []

class ControlMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    assessment_id: str
    framework_id: str
    control_id: str
    control_title: str
    control_category: str | None = None
    status: str
    evidence_summary: str | None = None
    rationale: str | None = None
    source_url: str | None = None
    is_conceptual: bool = False

class AssessmentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_name: str
    description: str | None = None
    status: str
    overall_risk_score: float
    risk_level: str
    compliance_score: float
    target_frameworks: list[str] = []
    findings_count: int
    severity_breakdown: dict[str, int] = {}
    compliance_breakdown: dict[str, int] = {}
    created_at: datetime
    completed_at: datetime | None = None

class AssessmentDetailResponse(AssessmentSummaryResponse):
    recon_summary: dict[str, Any] = {}
    findings: list[FindingResponse] = []
    control_mappings: list[ControlMappingResponse] = []

class ReportResponse(BaseModel):
    report_metadata: dict[str, Any]
    assessment_summary: AssessmentSummaryResponse
    recon_summary: dict[str, Any]
    findings: list[FindingResponse]
    compliance_matrix: list[ControlMappingResponse]
    remediation_roadmap: list[dict[str, Any]]
    disclaimer: str
