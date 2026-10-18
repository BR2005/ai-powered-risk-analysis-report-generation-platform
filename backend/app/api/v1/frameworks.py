from fastapi import APIRouter
from app.engine.compliance import ComplianceMapper
from app.schemas.assessment import FrameworkListResponse, FrameworkSchema, ControlSchema

router = APIRouter(prefix="/frameworks", tags=["Frameworks"])
mapper = ComplianceMapper()

@router.get("", response_model=FrameworkListResponse)
def get_frameworks():
    """Returns supported GenAI security and risk frameworks with control coverage."""
    fws = mapper.get_all_frameworks()
    formatted = []
    total_ctrls = 0
    for fw in fws:
        ctrls = [
            ControlSchema(
                control_id=c["control_id"],
                title=c["title"],
                category=c.get("category", ""),
                description=c["description"],
                reference_url=c.get("reference_url"),
                verification_guidance=c.get("verification_guidance"),
                is_conceptual_mapping=c.get("is_conceptual_mapping", False)
            )
            for c in fw.get("controls", [])
        ]
        total_ctrls += len(ctrls)
        formatted.append(FrameworkSchema(
            id=fw["id"],
            name=fw["name"],
            version=fw["version"],
            publisher=fw["publisher"],
            category=fw["category"],
            controls_count=len(ctrls),
            source_url=fw["source_url"],
            disclaimer=fw["disclaimer"],
            controls=ctrls
        ))

    return FrameworkListResponse(
        frameworks=formatted,
        total_frameworks=len(formatted),
        total_controls=total_ctrls
    )
