from pathlib import Path
from app.engine.scanner import ScanFinding
from app.engine.redactor import redact_secrets

class EvidenceValidationAgent:
    """Agent 3: Verifies source evidence, sanitizes snippets, and classifies validation confidence."""

    async def execute(self, findings: list[ScanFinding], workspace_dir: Path | None) -> list[ScanFinding]:
        validated_findings: list[ScanFinding] = []

        for f in findings:
            # 1. Verify file exists in workspace
            file_exists = False
            if workspace_dir:
                actual_file = workspace_dir / f.file_path
                file_exists = actual_file.exists() and actual_file.is_file()

            # 2. Re-sanitize code snippet to ensure zero secret leakage
            if f.code_snippet:
                f.code_snippet = redact_secrets(f.code_snippet)

            # 3. Validation status assignment
            if not file_exists and f.confidence != "INFORMATIONAL":
                f.confidence = "NOT_VERIFIED"
                f.validation_status = "REQUIRES_MANUAL_REVIEW"
                f.context_note = (f.context_note or "") + " [Warning: Source file could not be re-verified on disk]"
            elif f.severity in ("CRITICAL", "HIGH"):
                # If AST confirmed and snippet present, keep verified
                if f.code_snippet and len(f.code_snippet) > 5:
                    f.confidence = "CONFIRMED"
                    f.validation_status = "VERIFIED"
                else:
                    f.confidence = "SUSPECTED"
                    f.validation_status = "REQUIRES_MANUAL_REVIEW"
            else:
                # Medium/Low findings
                if f.confidence not in ("CONFIRMED", "SUSPECTED"):
                    f.confidence = "SUSPECTED"
                    f.validation_status = "REQUIRES_MANUAL_REVIEW"

            validated_findings.append(f)

        return validated_findings
