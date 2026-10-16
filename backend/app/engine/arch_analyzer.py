import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ArchitectureAnalysisResult:
    components: list[str] = field(default_factory=list)
    models_detected: list[str] = field(default_factory=list)
    vector_stores: list[str] = field(default_factory=list)
    tools_detected: list[str] = field(default_factory=list)
    trust_boundaries: list[str] = field(default_factory=list)
    documented_controls: list[str] = field(default_factory=list)
    unverified_claims: list[str] = field(default_factory=list)

class ArchitectureAnalyzer:
    """Extracts stated components, data flows, and trust boundaries from architecture docs and manual input."""

    def analyze_text(self, text: str) -> ArchitectureAnalysisResult:
        result = ArchitectureAnalysisResult()
        lower_text = text.lower()

        # 1. Models & Foundation APIs
        model_keywords = {
            "OpenAI (GPT-4 / GPT-3.5)": ["openai", "gpt-4", "gpt-3.5", "gpt4", "chatgpt"],
            "Anthropic Claude": ["claude", "anthropic"],
            "Meta LLaMA": ["llama", "llama-2", "llama-3", "llama3"],
            "Mistral AI": ["mistral", "mixtral"],
            "Google Gemini": ["gemini", "vertex ai"],
            "Local Ollama": ["ollama", "local llm"],
            "HuggingFace": ["huggingface", "transformers"],
        }
        for name, kws in model_keywords.items():
            if any(kw in lower_text for kw in kws):
                result.models_detected.append(name)
                result.components.append(f"Model Provider: {name}")

        # 2. Vector Stores & RAG
        vector_keywords = {
            "ChromaDB": ["chroma", "chromadb"],
            "Pinecone": ["pinecone"],
            "Qdrant": ["qdrant"],
            "Weaviate": ["weaviate"],
            "FAISS": ["faiss"],
            "PostgreSQL pgvector": ["pgvector", "postgres vector"],
        }
        for name, kws in vector_keywords.items():
            if any(kw in lower_text for kw in kws):
                result.vector_stores.append(name)
                result.components.append(f"Vector Database: {name}")

        # 3. Agent Frameworks & Tools
        tool_keywords = {
            "LangChain": ["langchain"],
            "LangGraph": ["langgraph"],
            "LlamaIndex": ["llamaindex", "llama_index"],
            "AutoGPT / CrewAI": ["crewai", "autogpt"],
            "OS Command Shell Tools": ["subprocess", "bash", "shell tool", "terminal"],
            "Web Browsing / Scraping Tool": ["requests", "playwright", "puppeteer", "web search", "beautifulsoup"],
            "Database SQL Tool": ["sql tool", "database query", "execute_sql"],
        }
        for name, kws in tool_keywords.items():
            if any(kw in lower_text for kw in kws):
                result.tools_detected.append(name)
                result.components.append(f"Agent Framework/Tool: {name}")

        # 4. Stated Security Controls
        control_keywords = {
            "Input Prompt Guardrails": ["guardrail", "prompt validation", "input filter", "nemo guardrails"],
            "Output Sanitization / HTML Escaping": ["output sanitization", "dompurify", "output validation", "html escape"],
            "Human-in-the-Loop Oversight": ["human in the loop", "hitl", "human approval", "manual approval"],
            "Role-Based Access Control (RBAC)": ["rbac", "role based", "access control", "tenant isolation"],
            "Secret Redaction / DLP": ["dlp", "pii masking", "secret redaction", "redaction"],
        }
        for name, kws in control_keywords.items():
            if any(kw in lower_text for kw in kws):
                result.documented_controls.append(name)
                # By default, mark as unverified claim until code scanner corroborates
                result.unverified_claims.append(f"Documented claim: '{name}' requires implementation verification in code.")

        # 5. Trust Boundaries
        if "external api" in lower_text or "third party" in lower_text:
            result.trust_boundaries.append("External Foundation Model API Boundary (Public Cloud / SaaS)")
        if "vector" in lower_text or "rag" in lower_text:
            result.trust_boundaries.append("RAG Knowledge Retrieval Boundary (Internal Knowledge vs Model Context)")
        if "tool" in lower_text or "agent" in lower_text:
            result.trust_boundaries.append("Autonomous Tool Execution Boundary (Agent Sandbox vs Host System)")
        if not result.trust_boundaries:
            result.trust_boundaries.append("User Input Boundary -> Application Controller -> LLM Inference Pipeline")

        return result

    def analyze_documentation_directory(self, target_dir: Path) -> ArchitectureAnalysisResult:
        combined_text = ""
        for file_path in target_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in (".md", ".txt", ".rst"):
                try:
                    combined_text += "\n" + file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    pass
        return self.analyze_text(combined_text)
