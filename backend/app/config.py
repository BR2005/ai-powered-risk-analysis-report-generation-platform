import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = BASE_DIR.parent
COMPLIANCE_RULES_DIR = Path(os.getenv("COMPLIANCE_RULES_DIR", "/compliance-rules" if Path("/compliance-rules").exists() else WORKSPACE_ROOT / "compliance-rules"))
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _resolve_database_url() -> str:
    raw = os.getenv("DATABASE_URL")
    if raw:
        # Render PostgreSQL URLs start with postgres://, SQLAlchemy 2 requires postgresql://
        if raw.startswith("postgres://"):
            return raw.replace("postgres://", "postgresql://", 1)
        # Handle SQLite paths
        if raw.startswith("sqlite"):
            if raw in ("sqlite:///./platform.db", "sqlite:///platform.db"):
                try:
                    db_path = BASE_DIR / "platform.db"
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                    test_f = db_path.parent / ".perm_check"
                    test_f.touch()
                    test_f.unlink()
                    return f"sqlite:///{db_path.as_posix()}"
                except Exception:
                    return "sqlite:////tmp/platform.db"
            return raw
        return raw

    # Default fallback
    try:
        db_path = BASE_DIR / "platform.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        test_f = db_path.parent / ".perm_check"
        test_f.touch()
        test_f.unlink()
        return f"sqlite:///{db_path.as_posix()}"
    except Exception:
        return "sqlite:////tmp/platform.db"

class Settings(BaseModel):
    app_name: str = "Lucifer: AI-Powered GenAI Security Risk & Compliance Platform"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: str = _resolve_database_url()

    # File limits
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    max_extracted_files: int = 500
    max_file_size_bytes: int = 5 * 1024 * 1024    # 5 MB per file
    allowed_extensions: set[str] = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
        ".md", ".txt", ".env", ".toml", ".ini", ".cfg", ".zip"
    }
    
    # LLM Settings - Configured for Gemma 4
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemma-4") # "gemma-4", "ollama", "openai-compatible", "fallback"
    gemma_model: str = os.getenv("GEMMA_MODEL", "gemma-4-12b-it") # e.g. gemma-4-12b-it, gemma-4-e4b, gemma-4-31b-it
    gemma_api_key: str | None = os.getenv("GEMMA_API_KEY", os.getenv("GEMINI_API_KEY", None))
    gemma_endpoint_type: str = os.getenv("GEMMA_ENDPOINT_TYPE", "google-ai-studio") # "google-ai-studio", "ollama", "custom"
    
    # Ollama settings (for local Gemma 4 runtime)
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma-4")
    
    # Custom / OpenAI-compatible endpoint (e.g. vLLM or Hugging Face endpoint serving Gemma 4)
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY", None)
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gemma-4-12b-it")
    
    # Paths
    compliance_rules_dir: Path = COMPLIANCE_RULES_DIR
    upload_dir: Path = UPLOAD_DIR

settings = Settings()
