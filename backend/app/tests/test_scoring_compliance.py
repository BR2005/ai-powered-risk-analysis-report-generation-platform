from app.engine.scoring import ScoringEngine
from app.engine.scanner import ScanFinding
from app.engine.compliance import ComplianceMapper

def test_scoring_engine():
    engine = ScoringEngine()

    # Empty findings -> Informational, 0 score
    score, level, breakdown = engine.calculate_risk([])
    assert score == 0.0
    assert level == "INFORMATIONAL"

    # Critical finding
    critical_finding = ScanFinding(
        finding_id="TEST-CRIT-01",
        title="Critical ACE",
        description="Arbitrary code execution",
        category="INSECURE_OUTPUT_HANDLING",
        severity="CRITICAL",
        numerical_score=9.8,
        confidence="CONFIRMED",
        validation_status="VERIFIED",
        owasp_id="LLM05",
        file_path="app.py"
    )

    score, level, breakdown = engine.calculate_risk([critical_finding])
    assert score >= 75.0
    assert level == "CRITICAL"
    assert breakdown["CRITICAL"] == 1

def test_compliance_mapper_control_classification():
    mapper = ComplianceMapper()
    
    # Finding for prompt injection
    pi_finding = ScanFinding(
        finding_id="TEST-PI-01",
        title="Prompt Injection",
        description="F-string in prompt",
        category="PROMPT_INJECTION",
        severity="HIGH",
        numerical_score=8.2,
        confidence="CONFIRMED",
        validation_status="VERIFIED",
        owasp_id="LLM01",
        file_path="agent.py"
    )

    mappings = mapper.evaluate_controls(
        findings=[pi_finding],
        target_frameworks=["OWASP-GENAI", "NIST-AI-RMF", "EU-AI-ACT"]
    )

    # OWASP LLM01 should be MISSING_WITH_EVIDENCE because high finding violates it
    owasp_llm01 = next(m for m in mappings if m["framework_id"] == "OWASP-GENAI" and m["control_id"] == "LLM01")
    assert owasp_llm01["status"] == "MISSING_WITH_EVIDENCE"

    # EU AI Act Article 15 (Cybersecurity & Robustness) crosswalked to Prompt Injection should be MISSING_WITH_EVIDENCE
    eu_art15 = next(m for m in mappings if m["framework_id"] == "EU-AI-ACT" and m["control_id"] == "EU-AI-ART-15")
    assert eu_art15["status"] == "MISSING_WITH_EVIDENCE"

    # Unaffected controls (e.g., EU-AI-ART-50 AI watermark transparency) should be NOT_EVIDENCED (absence of evidence, not missing!)
    eu_art50 = next(m for m in mappings if m["framework_id"] == "EU-AI-ACT" and m["control_id"] == "EU-AI-ART-50")
    assert eu_art50["status"] == "NOT_EVIDENCED"
