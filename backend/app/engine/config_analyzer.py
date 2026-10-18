import re
from pathlib import Path
from app.engine.scanner import ScanFinding
from app.engine.redactor import redact_secrets

class ConfigAnalyzer:
    """Analyzes configuration files, environment variables, and dependencies for security weaknesses."""

    def analyze_file(self, file_path: Path, relative_to: Path | None = None) -> list[ScanFinding]:
        findings: list[ScanFinding] = []
        rel_path = str(file_path.relative_to(relative_to)) if relative_to else str(file_path)
        filename = file_path.name.lower()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return findings

        # 1. Check .env file directly committed
        if filename.startswith(".env"):
            findings.append(ScanFinding(
                finding_id=f"CONFIG-ENV-{len(findings)+1:02d}",
                title="Environment Configuration File Detected in Repository",
                description=(
                    "A `.env` file was found in the application repository. "
                    "Committing active environment files increases the risk of exposing production API tokens and passwords."
                ),
                category="SENSITIVE_DATA_EXPOSURE",
                severity="MEDIUM",
                numerical_score=5.5,
                confidence="CONFIRMED",
                validation_status="VERIFIED",
                owasp_id="LLM02",
                file_path=rel_path,
                line_start=1,
                line_end=1,
                code_snippet=redact_secrets(content[:150]),
                context_note="Environment file found in repository root.",
                remediation="Add `.env` to `.gitignore`. Use a template file such as `.env.example` with dummy values for development.",
                remediation_snippet="# .gitignore entry\n.env\n.env.local\n*.env"
            ))

        # 2. Check for DEBUG mode enabled in settings / env
        if re.search(r"""(?i)^\s*DEBUG\s*=\s*(?:True|1|yes)\s*$""", content, re.MULTILINE):
            findings.append(ScanFinding(
                finding_id=f"CONFIG-DEBUG-{len(findings)+1:02d}",
                title="Debug Mode Enabled in Application Configuration",
                description="DEBUG mode is explicitly enabled. In production, this can expose interactive debuggers, stack traces, and environment secrets.",
                category="SECURITY_MISCONFIGURATION",
                severity="LOW",
                numerical_score=3.5,
                confidence="CONFIRMED",
                validation_status="VERIFIED",
                owasp_id="LLM02",
                file_path=rel_path,
                line_start=1,
                code_snippet="DEBUG=True",
                context_note="DEBUG flag active in configuration file.",
                remediation="Ensure DEBUG is disabled (DEBUG=False) in production and staging environments.",
                remediation_snippet="DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'"
            ))

        # 3. Check for wildcard CORS with credentials
        if re.search(r"""(?i)allow_origins\s*=\s*\[\s*["']\*["']\s*\]\s*,\s*allow_credentials\s*=\s*True""", content):
            findings.append(ScanFinding(
                finding_id=f"CONFIG-CORS-{len(findings)+1:02d}",
                title="Insecure Permissive CORS Configuration (Wildcard with Credentials)",
                description="CORS middleware configured with wildcard origin ('*') combined with allow_credentials=True. Browsers or malicious sites can forge cross-origin requests.",
                category="SECURITY_MISCONFIGURATION",
                severity="MEDIUM",
                numerical_score=6.0,
                confidence="CONFIRMED",
                validation_status="VERIFIED",
                owasp_id="LLM03",
                file_path=rel_path,
                line_start=1,
                code_snippet="allow_origins=['*'], allow_credentials=True",
                context_note="Permissive CORS settings detected.",
                remediation="Explicitly specify authorized frontend domains rather than using wildcard origins.",
                remediation_snippet="allow_origins=['https://app.example.com'], allow_credentials=True"
            ))

        return findings

    def analyze_directory(self, target_dir: Path) -> list[ScanFinding]:
        findings: list[ScanFinding] = []
        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() in (".env", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg") or file_path.name.startswith(".env"):
                    findings.extend(self.analyze_file(file_path, relative_to=target_dir))
        return findings
