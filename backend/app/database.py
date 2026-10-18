from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Handle sqlite specific connect args
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_assessment_tracking_columns(bind=engine) -> None:
    """Add the multi-agent tracking columns to databases created by older releases."""
    inspector = inspect(bind)
    if not inspector.has_table("assessments"):
        return

    columns = {column["name"] for column in inspector.get_columns("assessments")}
    migrations = {
        "agent_execution_log": "JSON DEFAULT '[]'",
        "supervisor_iterations": "INTEGER DEFAULT 0",
    }

    with bind.begin() as connection:
        for name, definition in migrations.items():
            if name not in columns:
                connection.execute(
                    text(f"ALTER TABLE assessments ADD COLUMN {name} {definition}")
                )
