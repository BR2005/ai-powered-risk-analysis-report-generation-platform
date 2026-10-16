import tempfile
from pathlib import Path
from app.engine.scanner import StaticScanner
from app.engine.redactor import redact_secrets

def test_secret_redactor():
    fake_key = "sk-1234567890abcdef1234567890abcdef"
    text = f'openai_api_key = "{fake_key}"'
    redacted = redact_secrets(text)
    assert fake_key not in redacted
    assert "REDACTED" in redacted

def test_static_scanner_ast_detection():
    vulnerable_code = '''
import os
import pickle

def handle_user_query(user_input):
    # Prompt injection
    prompt = f"Answer the user query: {user_input}"
    
    # Insecure output handling
    model_response = "print('hello')"
    eval(model_response)
    
    # Deserialization
    with open("weights.pkl", "rb") as f:
        pickle.load(f)
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "vuln_app.py"
        test_file.write_text(vulnerable_code)

        scanner = StaticScanner()
        findings = scanner.scan_directory(Path(tmpdir))

        categories = [f.category for f in findings]
        assert "PROMPT_INJECTION" in categories
        assert "INSECURE_OUTPUT_HANDLING" in categories
        assert "SUPPLY_CHAIN_VULNERABILITY" in categories
        
        # Verify severities and codes
        eval_finding = next(f for f in findings if f.category == "INSECURE_OUTPUT_HANDLING")
        assert eval_finding.severity == "CRITICAL"
        assert eval_finding.owasp_id == "LLM05"
