import ast
import re
from pathlib import Path
from dataclasses import dataclass, field
from app.engine.redactor import redact_secrets

@dataclass
class ScanFinding:
    finding_id: str
    title: str
    description: str
    category: str
    severity: str # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
    numerical_score: float # 0.0 - 10.0
    confidence: str # CONFIRMED, SUSPECTED, INFORMATIONAL, NOT_VERIFIED
    validation_status: str # VERIFIED, REQUIRES_MANUAL_REVIEW
    owasp_id: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    code_snippet: str | None = None
    context_note: str | None = None
    remediation: str | None = None
    remediation_snippet: str | None = None

class PythonAstVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.findings: list[ScanFinding] = []

    def _get_snippet(self, node: ast.AST) -> str:
        start = getattr(node, 'lineno', 1) - 1
        end = getattr(node, 'end_lineno', start + 1)
        lines = self.source_lines[start:end]
        return redact_secrets("\n".join(lines).strip())

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # 1. Insecure Output Handling: eval() or exec()
        if func_name in ("eval", "exec"):
            snippet = self._get_snippet(node)
            self.findings.append(ScanFinding(
                finding_id=f"FINDING-IOH-{len(self.findings)+1:02d}",
                title="Insecure Output Handling: Execution of Untrusted Code (eval/exec)",
                description=(
                    f"Direct invocation of `{func_name}()` was detected. If the input derives from an LLM "
                    "or user prompt, an adversary can achieve Arbitrary Code Execution (ACE) via prompt injection."
                ),
                category="INSECURE_OUTPUT_HANDLING",
                severity="CRITICAL",
                numerical_score=9.6,
                confidence="CONFIRMED",
                validation_status="VERIFIED",
                owasp_id="LLM05",
                file_path=self.file_path,
                line_start=node.lineno,
                line_end=getattr(node, 'end_lineno', node.lineno),
                code_snippet=snippet,
                context_note=f"Call to `{func_name}()` detected in Python AST.",
                remediation=(
                    "Avoid dynamic evaluation of generated output. Use structured output parsers "
                    "(e.g., Pydantic schemas, json.loads with schema validation) and sandboxed execution environments."
                ),
                remediation_snippet="# Replace eval/exec with validated schema parsing\nfrom pydantic import BaseModel\n\nparsed_data = MyResponseModel.model_validate_json(llm_output)"
            ))

        # 2. Deserialization Vulnerability: pickle.load or torch.load without weights_only
        if (isinstance(node.func, ast.Attribute) and node.func.attr == "load") or func_name == "load":
            call_repr = ast.unparse(node.func) if hasattr(ast, "unparse") else func_name
            if "pickle" in call_repr:
                snippet = self._get_snippet(node)
                self.findings.append(ScanFinding(
                    finding_id=f"FINDING-DESER-{len(self.findings)+1:02d}",
                    title="Insecure Model/Data Deserialization (pickle.load)",
                    description=(
                        "Loading untrusted data or model checkpoints with `pickle.load()` allows remote arbitrary code execution. "
                        "Adversaries can embed malicious payloads into serialized weights or embeddings."
                    ),
                    category="SUPPLY_CHAIN_VULNERABILITY",
                    severity="CRITICAL",
                    numerical_score=9.2,
                    confidence="CONFIRMED",
                    validation_status="VERIFIED",
                    owasp_id="LLM03",
                    file_path=self.file_path,
                    line_start=node.lineno,
                    line_end=getattr(node, 'end_lineno', node.lineno),
                    code_snippet=snippet,
                    context_note="Use of Python pickle.load() detected.",
                    remediation="Use secure model weight formats such as Safetensors or ONNX, avoiding Python pickle deserialization.",
                    remediation_snippet="# Use safetensors for model weights\nfrom safetensors.torch import load_file\nweights = load_file('model.safetensors')"
                ))
            elif "torch" in call_repr:
                # Check if weights_only=True is passed
                has_weights_only = any(kw.arg == "weights_only" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in node.keywords)
                if not has_weights_only:
                    snippet = self._get_snippet(node)
                    self.findings.append(ScanFinding(
                        finding_id=f"FINDING-TORCH-{len(self.findings)+1:02d}",
                        title="Unsafe PyTorch Checkpoint Loading Without weights_only=True",
                        description=(
                            "`torch.load()` invoked without `weights_only=True`. In PyTorch, default unpickling can execute arbitrary code "
                            "if an attacker supplies a tampered model checkpoint."
                        ),
                        category="SUPPLY_CHAIN_VULNERABILITY",
                        severity="HIGH",
                        numerical_score=8.1,
                        confidence="CONFIRMED",
                        validation_status="VERIFIED",
                        owasp_id="LLM03",
                        file_path=self.file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, 'end_lineno', node.lineno),
                        code_snippet=snippet,
                        context_note="torch.load() without weights_only=True keyword.",
                        remediation="Explicitly set weights_only=True when invoking torch.load() to prevent arbitrary code execution.",
                        remediation_snippet="model_weights = torch.load('model.pt', weights_only=True)"
                    ))

        # 3. Excessive Agency: System/Shell execution in agent tool functions
        if func_name in ("system", "popen") or (isinstance(node.func, ast.Attribute) and node.func.attr in ("system", "run", "Popen", "check_output")):
            call_repr = ast.unparse(node.func) if hasattr(ast, "unparse") else func_name
            if any(mod in call_repr for mod in ("os", "subprocess")):
                snippet = self._get_snippet(node)
                self.findings.append(ScanFinding(
                    finding_id=f"FINDING-AGENCY-{len(self.findings)+1:02d}",
                    title="Excessive Agency: Operating System Command Execution via Agent Tool",
                    description=(
                        f"Invocation of `{call_repr}()` detected. Granting LLM agents access to system command shells "
                        "without strict whitelisting and human-in-the-loop authorization creates severe remote command injection risks."
                    ),
                    category="EXCESSIVE_AGENCY",
                    severity="HIGH",
                    numerical_score=8.5,
                    confidence="SUSPECTED",
                    validation_status="REQUIRES_MANUAL_REVIEW",
                    owasp_id="LLM06",
                    file_path=self.file_path,
                    line_start=node.lineno,
                    line_end=getattr(node, 'end_lineno', node.lineno),
                    code_snippet=snippet,
                    context_note="OS shell execution detected in agent environment.",
                    remediation="Restrict agent capabilities to pre-approved read-only API functions. Require mandatory human confirmation for system commands.",
                    remediation_snippet="# Require human confirmation for sensitive tools\nif not request_user_confirmation(action):\n    raise PermissionError('Action cancelled by operator')"
                ))

        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        # f-strings: Check if f-string is used in prompt construction
        snippet = self._get_snippet(node)
        lower_snippet = snippet.lower()
        prompt_keywords = ("prompt", "system_prompt", "user_prompt", "human_message", "instruction", "template", "query")
        if any(kw in lower_snippet for kw in prompt_keywords) and any(isinstance(v, ast.FormattedValue) for v in node.values):
            self.findings.append(ScanFinding(
                finding_id=f"FINDING-PI-FSTR-{len(self.findings)+1:02d}",
                title="Prompt Injection Risk: Direct F-String Concatenation in Prompt Construction",
                description=(
                    "Dynamic variable interpolation into prompt string using Python f-strings detected. "
                    "Unsanitized user inputs concatenated directly into system or user prompts enable Direct Prompt Injection."
                ),
                category="PROMPT_INJECTION",
                severity="HIGH",
                numerical_score=8.2,
                confidence="CONFIRMED",
                validation_status="VERIFIED",
                owasp_id="LLM01",
                file_path=self.file_path,
                line_start=node.lineno,
                line_end=getattr(node, 'end_lineno', node.lineno),
                code_snippet=snippet,
                context_note="f-string formatting variables into prompt string.",
                remediation=(
                    "Separate system instructions from user inputs using structured message roles (SystemMessage, HumanMessage) "
                    "and sanitize untrusted inputs before inclusion."
                ),
                remediation_snippet=(
                    "# Use role-isolated prompt templates\n"
                    "messages = [\n"
                    "    {'role': 'system', 'content': 'You are an assistant. Answer questions truthfully.'},\n"
                    "    {'role': 'user', 'content': sanitize_input(user_input)}\n"
                    "]"
                )
            ))
        self.generic_visit(node)


class StaticScanner:
    """Multi-language static scanner analyzing GenAI applications for security risks."""

    def __init__(self):
        # Patterns for regex-based scans across files
        self.regex_rules = [
            # Hardcoded API keys
            {
                "id": "RULE-KEY-OPENAI",
                "pattern": re.compile(r"""(?i)(?:openai|anthropic|cohere|gemini|huggingface)[_-]?(?:api)?[_-]?key\s*=\s*["']([a-zA-Z0-9_\-]{20,})["']"""),
                "title": "Hardcoded AI Provider API Key Detected",
                "description": "Hardcoded AI provider secret credentials found in source code. Secrets can be exfiltrated or leaked via version control.",
                "category": "SENSITIVE_DATA_EXPOSURE",
                "severity": "CRITICAL",
                "numerical_score": 9.4,
                "confidence": "CONFIRMED",
                "validation_status": "VERIFIED",
                "owasp_id": "LLM02",
                "remediation": "Move API keys to secure environment variables or a secret vault (e.g., AWS Secrets Manager, HashiCorp Vault). Never commit secrets to code.",
                "remediation_snippet": "import os\napi_key = os.getenv('OPENAI_API_KEY')"
            },
            # SQL Injection via LLM Output
            {
                "id": "RULE-SQLI-LLM",
                "pattern": re.compile(r"""(?i)(?:cursor|db|connection|session)\.execute\s*\(\s*f?["'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?\{.*?(?:response|llm|output|result|completion).*?\}""", re.DOTALL),
                "title": "SQL Injection via Insecure Output Handling of LLM Response",
                "description": "Unsanitized LLM response interpolated directly into an SQL execution string. Adversaries can inject malicious SQL clauses via jailbreaks.",
                "category": "INSECURE_OUTPUT_HANDLING",
                "severity": "CRITICAL",
                "numerical_score": 9.5,
                "confidence": "CONFIRMED",
                "validation_status": "VERIFIED",
                "owasp_id": "LLM05",
                "remediation": "Never concatenate LLM outputs into raw SQL queries. Use parameterized queries or safe ORM filters with strict schema constraints.",
                "remediation_snippet": "cursor.execute('SELECT * FROM items WHERE category = %s', (validated_category,))"
            },
            # Unfiltered Vector Search
            {
                "id": "RULE-RAG-UNFILTERED",
                "pattern": re.compile(r"""(?i)(?:similarity_search|search|query)\s*\(\s*(?:query|user_input|question)\s*\)(?!\s*,\s*filter)"""),
                "title": "Vector Store Query Missing Access Control / Tenant Filter",
                "description": "Vector similarity search executed without tenant or access-control metadata filters. This can lead to unauthorized data retrieval across organizational boundaries in multitenant RAG applications.",
                "category": "VECTOR_EMBEDDING_WEAKNESS",
                "severity": "MEDIUM",
                "numerical_score": 6.5,
                "confidence": "SUSPECTED",
                "validation_status": "REQUIRES_MANUAL_REVIEW",
                "owasp_id": "LLM08",
                "remediation": "Apply authorization filter expressions at similarity search retrieval time to ensure users only retrieve documents within their permission scope.",
                "remediation_snippet": "vector_store.similarity_search(query, filter={'tenant_id': current_user.tenant_id})"
            },
            # Sensitive prompt logging
            {
                "id": "RULE-LOG-PROMPT",
                "pattern": re.compile(r"""(?i)(?:logging|logger|print)\.(?:info|debug|warning|log)\s*\(\s*f?["'].*?(?:prompt|password|auth|token|secret).*?\{""", re.DOTALL),
                "title": "Potential Sensitive Information Disclosure in Application Logs",
                "description": "Application logs prompt contents or credentials without prior redaction. Log aggregation systems can expose sensitive PII and secrets to unauthorized log viewers.",
                "category": "SENSITIVE_DATA_EXPOSURE",
                "severity": "LOW",
                "numerical_score": 3.8,
                "confidence": "SUSPECTED",
                "validation_status": "REQUIRES_MANUAL_REVIEW",
                "owasp_id": "LLM02",
                "remediation": "Implement an automated PII/Secret scrubbing filter before writing logs to storage or observability pipelines.",
                "remediation_snippet": "logger.info('Received prompt', extra={'sanitized_length': len(prompt)})"
            },
            # React dangerouslySetInnerHTML with LLM output
            {
                "id": "RULE-XSS-LLM",
                "pattern": re.compile(r"""(?i)dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:\s*(?:response|llm|content|output|botResponse|markdown)"""),
                "title": "Cross-Site Scripting (XSS) via Insecure Output Rendering",
                "description": "LLM response rendered directly into DOM using dangerouslySetInnerHTML without HTML sanitization. Injected HTML or JavaScript payloads will execute in user browsers.",
                "category": "INSECURE_OUTPUT_HANDLING",
                "severity": "HIGH",
                "numerical_score": 8.4,
                "confidence": "CONFIRMED",
                "validation_status": "VERIFIED",
                "owasp_id": "LLM05",
                "remediation": "Sanitize HTML using DOMPurify before rendering, or use safe markdown rendering components that disable raw HTML.",
                "remediation_snippet": "import DOMPurify from 'dompurify';\n<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(response) }} />"
            },
            # Client-controlled URL passed to an outbound request
            {
                "id": "RULE-SSRF-USER-URL",
                "pattern": re.compile(r"""(?i)(?:requests\.(?:get|post|put|delete|request)|httpx\.(?:get|post|put|delete|request)|fetch|urlopen)\s*\(\s*(?:request\.(?:args|query|query_params|url|body)|req\.(?:query|params|body)|(?:user|untrusted|external|target)_url)\b"""),
                "title": "Potential Server-Side Request Forgery via Client-Controlled URL",
                "description": "A URL that appears to originate from request data is passed to an outbound HTTP request. Without destination validation, this may allow requests to unintended internal or external services.",
                "category": "SSRF_RISK",
                "severity": "HIGH",
                "numerical_score": 8.0,
                "confidence": "SUSPECTED",
                "validation_status": "REQUIRES_MANUAL_REVIEW",
                "owasp_id": "API7:2023",
                "remediation": "Validate outbound destinations against an explicit allowlist, reject private and link-local addresses, and re-check redirects.",
                "remediation_snippet": "if parsed_url.hostname not in ALLOWED_HOSTS:\n    raise ValueError('Destination is not allowed')"
            },
            # Disabled TLS certificate validation
            {
                "id": "RULE-TLS-VERIFY-DISABLED",
                "pattern": re.compile(r"""(?i)(?:verify\s*=\s*False|rejectUnauthorized\s*:\s*false)"""),
                "title": "TLS Certificate Verification Disabled",
                "description": "TLS certificate validation is disabled. This can allow an attacker to intercept or modify traffic.",
                "category": "SECURITY_MISCONFIGURATION",
                "severity": "HIGH",
                "numerical_score": 8.0,
                "confidence": "CONFIRMED",
                "validation_status": "VERIFIED",
                "owasp_id": "A02:2025",
                "remediation": "Enable certificate validation and configure a trusted certificate authority instead of disabling TLS verification.",
                "remediation_snippet": "response = requests.get(url, verify=True)"
            }
        ]

    def scan_file(self, file_path: Path, relative_to: Path | None = None) -> list[ScanFinding]:
        findings: list[ScanFinding] = []
        rel_path = str(file_path.relative_to(relative_to)) if relative_to else str(file_path)

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return findings

        lines = content.splitlines()

        # 1. Python AST Scan
        if file_path.suffix.lower() == ".py":
            try:
                tree = ast.parse(content, filename=rel_path)
                visitor = PythonAstVisitor(rel_path, lines)
                visitor.visit(tree)
                findings.extend(visitor.findings)
            except SyntaxError:
                # Fallback to regex if file has syntax error
                pass

        # 2. Regex Rule Scans (Python, JS, TS, Configs)
        for rule in self.regex_rules:
            for match in rule["pattern"].finditer(content):
                # Calculate line number
                start_char = match.start()
                line_no = content[:start_char].count("\n") + 1
                matched_text = match.group(0)
                snippet = redact_secrets(matched_text.strip())

                finding = ScanFinding(
                    finding_id=f"{rule['id']}-{len(findings)+1:02d}",
                    title=rule["title"],
                    description=rule["description"],
                    category=rule["category"],
                    severity=rule["severity"],
                    numerical_score=rule["numerical_score"],
                    confidence=rule["confidence"],
                    validation_status=rule["validation_status"],
                    owasp_id=rule["owasp_id"],
                    file_path=rel_path,
                    line_start=line_no,
                    line_end=line_no + matched_text.count("\n"),
                    code_snippet=snippet,
                    context_note=f"Matched security signature `{rule['id']}`.",
                    remediation=rule["remediation"],
                    remediation_snippet=rule["remediation_snippet"]
                )
                findings.append(finding)

        return findings

    def scan_directory(self, target_dir: Path) -> list[ScanFinding]:
        all_findings: list[ScanFinding] = []
        for file_path in target_dir.rglob("*"):
            if file_path.is_file() and not any(part.startswith(".") for part in file_path.parts):
                if file_path.suffix.lower() in (".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml", ".env"):
                    file_findings = self.scan_file(file_path, relative_to=target_dir)
                    all_findings.extend(file_findings)
        return all_findings
