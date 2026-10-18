from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.assessment import Finding
from app.schemas.assessment import FindingResponse

router = APIRouter(
    prefix="/findings",
    tags=["Findings"],
)

@router.get("", response_model=list[FindingResponse])
def get_findings(
    assessment_id: str | None = Query(None, description="Filter findings by assessment ID"),
    severity: str | None = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL)"),
    category: str | None = Query(None, description="Filter by risk category"),
    validation_status: str | None = Query(None, description="Filter by validation status"),
    db: Session = Depends(get_db)
):
    """Filters findings across assessments by severity, category, status, and assessment ID."""
    query = db.query(Finding)

    if assessment_id:
        query = query.filter(Finding.assessment_id == assessment_id)
    if severity:
        query = query.filter(Finding.severity == severity.upper())
    if category:
        query = query.filter(Finding.category == category.upper())
    if validation_status:
        query = query.filter(Finding.validation_status == validation_status.upper())

    findings = query.order_by(Finding.numerical_score.desc()).all()
    return findings
