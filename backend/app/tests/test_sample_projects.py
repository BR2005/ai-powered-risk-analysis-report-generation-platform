from pathlib import Path
from app.config import WORKSPACE_ROOT
from app.engine.scanner import StaticScanner
from app.engine.scoring import ScoringEngine

def test_sample_projects_scanner_benchmark():
    scanner = StaticScanner()
    scoring = ScoringEngine()

    insecure_dir = WORKSPACE_ROOT / "sample-projects" / "insecure-rag-agent"
    secure_dir = WORKSPACE_ROOT / "sample-projects" / "secure-rag-agent"

    assert insecure_dir.exists()
    assert secure_dir.exists()

    # 1. Scan insecure sample
    insecure_findings = scanner.scan_directory(insecure_dir)
    assert len(insecure_findings) >= 4

    categories = [f.category for f in insecure_findings]
    assert "PROMPT_INJECTION" in categories
    assert "INSECURE_OUTPUT_HANDLING" in categories
    assert "SUPPLY_CHAIN_VULNERABILITY" in categories
    assert "SENSITIVE_DATA_EXPOSURE" in categories

    score_insecure, level_insecure, _ = scoring.calculate_risk(insecure_findings)
    assert score_insecure >= 75.0
    assert level_insecure == "CRITICAL"

    # 2. Scan secure sample
    secure_findings = scanner.scan_directory(secure_dir)
    assert len(secure_findings) == 0

    score_secure, level_secure, _ = scoring.calculate_risk(secure_findings)
    assert score_secure == 0.0
    assert level_secure == "INFORMATIONAL"
