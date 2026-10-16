import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = BASE_DIR.parent
COMPLIANCE_RULES_DIR = WORKSPACE_ROOT / "compliance-rules"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "AI-Powered GenAI Security Risk & Compliance Platform"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/platform.db")
    
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
