import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING") # PENDING, SCANNING, ANALYZING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    
    # Deterministic Scores
    overall_risk_score = Column(Float, default=0.0) # 0 to 100
    risk_level = Column(String(50), default="INFORMATIONAL") # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
    compliance_score = Column(Float, default=0.0) # 0 to 100
    
    # Frameworks evaluated (e.g. ["OWASP-GENAI", "NIST-AI-RMF", ...])
    target_frameworks = Column(JSON, default=list)
    
    # Reconnaissance / Architecture extraction summary
    recon_summary = Column(JSON, default=dict)
    
    # Aggregate statistics
    findings_count = Column(Integer, default=0)
    severity_breakdown = Column(JSON, default=dict)
    compliance_breakdown = Column(JSON, default=dict)

    # Multi-agent workflow tracking (Gemma 4 supervisor decisions)
    agent_execution_log = Column(JSON, default=list)   # list of AgentExecutionRecord dicts
    supervisor_iterations = Column(Integer, default=0)  # total Gemma 4 routing calls
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    findings = relationship("Finding", back_populates="assessment", cascade="all, delete-orphan")
    control_mappings = relationship("ControlMapping", back_populates="assessment", cascade="all, delete-orphan")
    artifacts = relationship("AssessmentArtifact", back_populates="assessment", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    
    finding_id = Column(String(50), nullable=False) # e.g. FINDING-PI-01, FINDING-KEY-01
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False) # PROMPT_INJECTION, INSECURE_OUTPUT_HANDLING, etc.
    
    # Severity & Deterministic Score
    severity = Column(String(50), nullable=False) # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
    numerical_score = Column(Float, nullable=False, default=5.0) # 0.0 - 10.0
    confidence = Column(String(50), default="CONFIRMED") # CONFIRMED, SUSPECTED, INFORMATIONAL, NOT_VERIFIED
    validation_status = Column(String(50), default="VERIFIED") # VERIFIED, REQUIRES_MANUAL_REVIEW
    
    # OWASP GenAI Mapping
    owasp_id = Column(String(20), nullable=True)
    
    # Actionable Remediation
    remediation = Column(Text, nullable=True)
    remediation_snippet = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assessment = relationship("Assessment", back_populates="findings")
    evidences = relationship("Evidence", back_populates="finding", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    
    file_path = Column(String(500), nullable=False)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    context_note = Column(Text, nullable=True)
    is_redacted = Column(Boolean, default=True)

    finding = relationship("Finding", back_populates="evidences")


class ControlMapping(Base):
    __tablename__ = "control_mappings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    
    framework_id = Column(String(50), nullable=False) # OWASP-GENAI, NIST-AI-RMF, etc.
    control_id = Column(String(50), nullable=False)   # LLM01, MEASURE-2.5, etc.
    control_title = Column(String(255), nullable=False)
    control_category = Column(String(100), nullable=True)
    
    # Control status classification (Strictly supported types)
    status = Column(String(50), nullable=False, default="NOT_EVIDENCED")
    # Allowed: IMPLEMENTED_WITH_EVIDENCE, PARTIALLY_IMPLEMENTED, MISSING_WITH_EVIDENCE, NOT_EVIDENCED, NOT_APPLICABLE
    
    evidence_summary = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)
    is_conceptual = Column(Boolean, default=False)
    
    assessment = relationship("Assessment", back_populates="control_mappings")


class AssessmentArtifact(Base):
    __tablename__ = "assessment_artifacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False) # zip, python, config, doc, manual_text
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assessment = relationship("Assessment", back_populates="artifacts")
