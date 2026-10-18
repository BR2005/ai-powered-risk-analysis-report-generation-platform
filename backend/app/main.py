from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.v1.assessments import router as assessments_router
from app.api.v1.frameworks import router as frameworks_router
from app.api.v1.findings import router as findings_router
from app.schemas.assessment import HealthResponse

from sqlalchemy import text

# Create database tables automatically
Base.metadata.create_all(bind=engine)

# Auto-migrate SQLite columns if table already existed prior to multi-agent upgrade
try:
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(assessments)"))
        cols = {row[1] for row in result.fetchall()}
        if cols:
            if "agent_execution_log" not in cols:
                conn.execute(text("ALTER TABLE assessments ADD COLUMN agent_execution_log JSON DEFAULT '[]'"))
                conn.commit()
            if "supervisor_iterations" not in cols:
                conn.execute(text("ALTER TABLE assessments ADD COLUMN supervisor_iterations INTEGER DEFAULT 0"))
                conn.commit()
except Exception:
    pass

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
    allow_origins=["*"],
    allow_credentials=True,
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
