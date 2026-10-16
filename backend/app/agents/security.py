from pathlib import Path
from app.engine.scanner import StaticScanner, ScanFinding
from app.engine.config_analyzer import ConfigAnalyzer

class SecurityAnalysisAgent:
    """Agent 2: Interprets scanner findings and identifies relevant GenAI security vulnerabilities."""

    def __init__(self):
        self.code_scanner = StaticScanner()
        self.config_analyzer = ConfigAnalyzer()

    async def execute(self, workspace_dir: Path | None) -> list[ScanFinding]:
        if not workspace_dir or not workspace_dir.exists():
            return []

        findings: list[ScanFinding] = []

        # 1. Run static code analysis (AST and regex)
        code_findings = self.code_scanner.scan_directory(workspace_dir)
        findings.extend(code_findings)

        # 2. Run configuration and dependency analysis
        config_findings = self.config_analyzer.analyze_directory(workspace_dir)
        findings.extend(config_findings)

        # Deduplicate findings by file_path, line_start, and rule
        unique_findings: dict[str, ScanFinding] = {}
        for f in findings:
            key = f"{f.file_path}:{f.line_start}:{f.category}:{f.title}"
            if key not in unique_findings:
                unique_findings[key] = f

        return list(unique_findings.values())
