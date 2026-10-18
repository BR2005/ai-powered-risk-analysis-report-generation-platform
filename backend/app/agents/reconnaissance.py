from pathlib import Path
from typing import Any
from app.engine.arch_analyzer import ArchitectureAnalyzer, ArchitectureAnalysisResult
from app.agents.llm_provider import llm_provider

class ReconnaissanceAgent:
    """Agent 1: Summarizes the application's components, models, data flows, and trust boundaries."""

    def __init__(self):
        self.analyzer = ArchitectureAnalyzer()

    async def execute(self, architecture_text: str | None, workspace_dir: Path | None) -> dict[str, Any]:
        # 1. Deterministic base extraction from code and docs
        result = ArchitectureAnalysisResult()
        
        if architecture_text:
            text_res = self.analyzer.analyze_text(architecture_text)
            result.components.extend(text_res.components)
            result.models_detected.extend(text_res.models_detected)
            result.vector_stores.extend(text_res.vector_stores)
            result.tools_detected.extend(text_res.tools_detected)
            result.trust_boundaries.extend(text_res.trust_boundaries)
            result.documented_controls.extend(text_res.documented_controls)
            result.unverified_claims.extend(text_res.unverified_claims)

        if workspace_dir and workspace_dir.exists():
            doc_res = self.analyzer.analyze_documentation_directory(workspace_dir)
            result.components.extend([c for c in doc_res.components if c not in result.components])
            result.models_detected.extend([m for m in doc_res.models_detected if m not in result.models_detected])
            result.vector_stores.extend([v for v in doc_res.vector_stores if v not in result.vector_stores])
            result.tools_detected.extend([t for t in doc_res.tools_detected if t not in result.tools_detected])
            result.trust_boundaries.extend([b for b in doc_res.trust_boundaries if b not in result.trust_boundaries])
            result.documented_controls.extend([dc for dc in doc_res.documented_controls if dc not in result.documented_controls])
            result.unverified_claims.extend([uc for uc in doc_res.unverified_claims if uc not in result.unverified_claims])

        # If nothing detected, provide sane defaults for GenAI pipeline
        if not result.components:
            result.components = ["Core Application API", "LLM Inference Pipeline", "Context Assembly Pipeline"]
        if not result.trust_boundaries:
            result.trust_boundaries = ["Untrusted Client Input -> API Gateway -> Agent Prompt Orchestrator"]

        summary = {
            "components": list(dict.fromkeys(result.components)),
            "models_detected": list(dict.fromkeys(result.models_detected)),
            "vector_stores": list(dict.fromkeys(result.vector_stores)),
            "tools_detected": list(dict.fromkeys(result.tools_detected)),
            "trust_boundaries": list(dict.fromkeys(result.trust_boundaries)),
            "documented_controls": list(dict.fromkeys(result.documented_controls)),
            "unverified_claims": list(dict.fromkeys(result.unverified_claims)),
            "narrative_overview": (
                f"Application integrates {len(result.models_detected) or 1} foundation model interface(s), "
                f"{len(result.vector_stores)} vector retrieval source(s), and {len(result.tools_detected)} agent tool integration(s). "
                f"Security perimeter includes {len(result.trust_boundaries)} principal trust boundary transitions."
            )
        }

        # Optional LLM enrichment if available (never overrides deterministic lists)
        llm_enrichment = await llm_provider.generate_completion(
            system_prompt="You are a GenAI Application Security Architect. Summarize the application trust boundaries succinctly.",
            user_prompt=f"Analyze these components: {summary['components']} and boundaries: {summary['trust_boundaries']}"
        )
        if llm_enrichment:
            summary["llm_architectural_notes"] = llm_enrichment

        return summary
