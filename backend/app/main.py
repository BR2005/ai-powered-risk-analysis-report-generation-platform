from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, ensure_assessment_tracking_columns
from app.api.v1.assessments import router as assessments_router
from app.api.v1.frameworks import router as frameworks_router
from app.api.v1.findings import router as findings_router
from app.schemas.assessment import HealthResponse

# Create database tables automatically
Base.metadata.create_all(bind=engine)
ensure_assessment_tracking_columns()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Independent academic GenAI security risk assessment & compliance mapping platform.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Returns platform operational health, version, and database connectivity."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            pass
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        engine=f"Gemma 4 ({settings.gemma_model}) + Crosswalk Pipeline"
    )

# Register API v1 routers
app.include_router(frameworks_router, prefix=settings.api_v1_prefix)
app.include_router(assessments_router, prefix=settings.api_v1_prefix)
app.include_router(findings_router, prefix=settings.api_v1_prefix)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
