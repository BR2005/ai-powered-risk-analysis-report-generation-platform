import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.assessment import (
    Assessment,
    Finding,
    Evidence,
    ControlMapping,
    AssessmentArtifact
)
from app.schemas.assessment import (
    AssessmentCreateRequest,
    AssessmentSummaryResponse,
    AssessmentDetailResponse,
    ReportResponse
)
from app.utils.file_security import (
    safe_extract_zip,
    validate_uploaded_file_size,
    is_allowed_file,
    temporary_workspace,
    FileSecurityError
)
from app.agents.orchestrator import orchestrator
from app.utils.pdf_generator import generate_pdf_report

router = APIRouter(prefix="/assessments", tags=["Assessments"])

def _persist_assessment_results(
    db: Session,
    assessment: Assessment,
    pipeline_results: dict
):
    """Saves pipeline results, findings, evidence, and control mappings to DB."""
    recon = pipeline_results["recon_summary"]
    risk = pipeline_results["risk_result"]
    comp = pipeline_results["compliance_result"]
    raw_findings = pipeline_results["findings"]
    control_mappings_data = comp["control_mappings"]

    assessment.status = "COMPLETED"
    assessment.completed_at = datetime.now(timezone.utc)
    assessment.overall_risk_score = risk["overall_risk_score"]
    assessment.risk_level = risk["risk_level"]
    assessment.compliance_score = comp["compliance_score"]
    assessment.findings_count = len(raw_findings)
    assessment.severity_breakdown = risk["severity_breakdown"]
    assessment.compliance_breakdown = comp["compliance_breakdown"]
    assessment.recon_summary = recon

    # Save findings and evidence
    for rf in raw_findings:
        f_model = Finding(
            assessment_id=assessment.id,
            finding_id=rf.finding_id,
            title=rf.title,
            description=rf.description,
            category=rf.category,
            severity=rf.severity,
            numerical_score=rf.numerical_score,
            confidence=rf.confidence,
            validation_status=rf.validation_status,
            owasp_id=rf.owasp_id,
            remediation=rf.remediation,
            remediation_snippet=rf.remediation_snippet
        )
        db.add(f_model)
        db.flush() # obtain f_model.id

        ev_model = Evidence(
            finding_id=f_model.id,
            file_path=rf.file_path,
            line_start=rf.line_start,
            line_end=rf.line_end,
            code_snippet=rf.code_snippet,
            context_note=rf.context_note,
            is_redacted=True
        )
        db.add(ev_model)

    # Save control mappings
    for cm in control_mappings_data:
        cm_model = ControlMapping(
            assessment_id=assessment.id,
            framework_id=cm["framework_id"],
            control_id=cm["control_id"],
            control_title=cm["control_title"],
            control_category=cm.get("control_category"),
            status=cm["status"],
            evidence_summary=cm.get("evidence_summary"),
            rationale=cm.get("rationale"),
            source_url=cm.get("source_url"),
            is_conceptual=cm.get("is_conceptual", False)
        )
        db.add(cm_model)

    db.commit()
    db.refresh(assessment)

@router.post("", response_model=AssessmentDetailResponse)
async def create_assessment(
    request: AssessmentCreateRequest,
    db: Session = Depends(get_db)
):
    """Initiates an assessment based on architecture description and configuration."""
    assessment = Assessment(
        project_name=request.project_name,
        description=request.description,
        status="ANALYZING",
        target_frameworks=request.target_frameworks
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    try:
        results = await orchestrator.run_pipeline(
            project_name=request.project_name,
            architecture_text=request.architecture_text,
            workspace_dir=None,
            target_frameworks=request.target_frameworks
        )
        _persist_assessment_results(db, assessment, results)
        return assessment
    except Exception as e:
        assessment.status = "FAILED"
        assessment.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Assessment processing failed: {str(e)}")

@router.post("/upload", response_model=AssessmentDetailResponse)
async def upload_and_assess(
    file: UploadFile = File(...),
    project_name: str = Form(...),
    description: str | None = Form(None),
    architecture_text: str | None = Form(None),
    target_frameworks: str | None = Form(None),
    db: Session = Depends(get_db)
):
    """Accepts ZIP archives or source/doc files, validates them securely, and executes assessment."""
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension for '{file.filename}'. Allowed: {', '.join(settings.allowed_extensions)}"
        )

    # Parse target frameworks json if provided
    frameworks_list = ["OWASP-GENAI", "NIST-AI-RMF", "MITRE-ATLAS", "ISO-42001", "ISO-23894", "EU-AI-ACT"]
    if target_frameworks:
        try:
            frameworks_list = json.loads(target_frameworks)
        except Exception:
            frameworks_list = [f.strip() for f in target_frameworks.split(",") if f.strip()]

    # Read uploaded file bytes securely
    contents = await file.read()
    validate_uploaded_file_size(len(contents))

    assessment = Assessment(
        project_name=project_name,
        description=description,
        status="SCANNING",
        target_frameworks=frameworks_list
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    with temporary_workspace() as ws_dir:
        # Save uploaded artifact record
        saved_file_path = ws_dir / file.filename
        saved_file_path.write_bytes(contents)

        artifact = AssessmentArtifact(
            assessment_id=assessment.id,
            filename=file.filename,
            file_type="zip" if file.filename.lower().endswith(".zip") else Path(file.filename).suffix.lstrip("."),
            file_size=len(contents),
            storage_path=str(saved_file_path)
        )
        db.add(artifact)
        db.commit()

        # If it's a zip archive, extract safely
        extracted_dir = ws_dir / "extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)
        
        if file.filename.lower().endswith(".zip"):
            try:
                safe_extract_zip(saved_file_path, extracted_dir)
            except FileSecurityError as fse:
                assessment.status = "FAILED"
                assessment.error_message = f"Security error in ZIP archive: {str(fse)}"
                db.commit()
                raise HTTPException(status_code=400, detail=str(fse))
        else:
            # Single file: copy into extracted dir for scanning
            dest = extracted_dir / file.filename
            shutil.copy2(saved_file_path, dest)

        # Run pipeline
        try:
            assessment.status = "ANALYZING"
            db.commit()

            results = await orchestrator.run_pipeline(
                project_name=project_name,
                architecture_text=architecture_text,
                workspace_dir=extracted_dir,
                target_frameworks=frameworks_list
            )
            _persist_assessment_results(db, assessment, results)
            return assessment
        except Exception as e:
            assessment.status = "FAILED"
            assessment.error_message = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")

@router.get("", response_model=list[AssessmentSummaryResponse])
def list_assessments(db: Session = Depends(get_db)):
    """Lists previous assessments ordered by creation timestamp."""
    return db.query(Assessment).order_by(Assessment.created_at.desc()).all()

@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Returns assessment status, findings, scores, evidence, and control mappings."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")
    return assessment

@router.get("/{assessment_id}/report", response_model=ReportResponse)
async def get_assessment_report(assessment_id: str, db: Session = Depends(get_db)):
    """Generates structured JSON report according to academic assessment schema."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")

    findings_data = [
        {
            "id": f.id,
            "assessment_id": f.assessment_id,
            "finding_id": f.finding_id,
            "title": f.title,
            "description": f.description,
            "category": f.category,
            "severity": f.severity,
            "numerical_score": f.numerical_score,
            "confidence": f.confidence,
            "validation_status": f.validation_status,
            "owasp_id": f.owasp_id,
            "remediation": f.remediation,
            "remediation_snippet": f.remediation_snippet,
            "created_at": f.created_at,
            "evidences": [
                {
                    "id": ev.id,
                    "file_path": ev.file_path,
                    "line_start": ev.line_start,
                    "line_end": ev.line_end,
                    "code_snippet": ev.code_snippet,
                    "context_note": ev.context_note,
                    "is_redacted": ev.is_redacted
                }
                for ev in f.evidences
            ]
        }
        for f in assessment.findings
    ]

    control_mappings_data = [
        {
            "id": cm.id,
            "assessment_id": cm.assessment_id,
            "framework_id": cm.framework_id,
            "control_id": cm.control_id,
            "control_title": cm.control_title,
            "control_category": cm.control_category,
            "status": cm.status,
            "evidence_summary": cm.evidence_summary,
            "rationale": cm.rationale,
            "source_url": cm.source_url,
            "is_conceptual": cm.is_conceptual
        }
        for cm in assessment.control_mappings
    ]

    # Generate remediation roadmap
    from app.agents.remediation import RemediationAgent
    remediation_agent = RemediationAgent()
    from app.engine.scanner import ScanFinding
    scan_findings_proxy = [
        ScanFinding(
            finding_id=f.finding_id,
            title=f.title,
            description=f.description,
            category=f.category,
            severity=f.severity,
            numerical_score=f.numerical_score,
            confidence=f.confidence,
            validation_status=f.validation_status,
            owasp_id=f.owasp_id or "",
            file_path=f.evidences[0].file_path if f.evidences else "",
            line_start=f.evidences[0].line_start if f.evidences else None,
            remediation=f.remediation,
            remediation_snippet=f.remediation_snippet
        )
        for f in assessment.findings
    ]
    remediation_roadmap = await remediation_agent.execute(scan_findings_proxy, control_mappings_data)

    report_metadata = {
        "report_id": f"REP-{assessment.id[:8].upper()}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform_name": settings.app_name,
        "platform_version": settings.app_version,
        "assessment_id": assessment.id,
        "project_name": assessment.project_name
    }

    return ReportResponse(
        report_metadata=report_metadata,
        assessment_summary=AssessmentSummaryResponse.model_validate(assessment),
        recon_summary=assessment.recon_summary or {},
        findings=findings_data,
        compliance_matrix=control_mappings_data,
        remediation_roadmap=remediation_roadmap,
        disclaimer=(
            "Independent academic assessment aid inspired by OWASP GenAI Security Crosswalk. "
            "Does not constitute legal compliance certification."
        )
    )

@router.get("/{assessment_id}/report.pdf")
def get_pdf_report(assessment_id: str, db: Session = Depends(get_db)):
    """Generates and downloads a cybersecurity assessment audit report in PDF format."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")

    findings_data = [
        {
            "finding_id": f.finding_id,
            "title": f.title,
            "description": f.description,
            "severity": f.severity,
            "remediation": f.remediation,
            "evidences": [
                {
                    "file_path": ev.file_path,
                    "line_start": ev.line_start,
                    "code_snippet": ev.code_snippet
                }
                for ev in f.evidences
            ]
        }
        for f in assessment.findings
    ]

    control_mappings_data = [
        {
            "framework_id": cm.framework_id,
            "control_id": cm.control_id,
            "control_title": cm.control_title,
            "status": cm.status
        }
        for cm in assessment.control_mappings
    ]

    report_dict = {
        "id": assessment.id,
        "project_name": assessment.project_name,
        "overall_risk_score": assessment.overall_risk_score,
        "risk_level": assessment.risk_level,
        "compliance_score": assessment.compliance_score,
        "findings_count": assessment.findings_count,
        "severity_breakdown": assessment.severity_breakdown or {},
        "recon_summary": assessment.recon_summary or {},
        "findings": findings_data,
        "control_mappings": control_mappings_data
    }

    pdf_bytes = generate_pdf_report(report_dict)

    filename = f"GenAI_Security_Report_{assessment.project_name.replace(' ', '_')}_{assessment.id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )
