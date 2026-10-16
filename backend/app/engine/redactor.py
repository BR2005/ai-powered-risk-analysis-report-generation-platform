import re

# Common API key and secret patterns
SECRET_PATTERNS = [
    # OpenAI & typical sk- keys
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "sk-***[REDACTED_API_KEY]***"),
    # AWS Access Keys
    (re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}", re.ASCII), "[REDACTED_AWS_KEY]"),
    # Generic bearer tokens
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{25,}", re.IGNORECASE), r"\1[REDACTED_BEARER_TOKEN]"),
    # GitHub personal access tokens
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
    # Generic key assignment in code or env
    (re.compile(r"""(?i)(api[_-]?key|secret|password|token|access[_-]?token)\s*[:=]\s*["']([^"']{8,})["']"""), r'\1: "[REDACTED_SECRET]"'),
]

def redact_secrets(text: str | None) -> str:
    """Redacts known secret formats and credential patterns from code snippets and logs."""
    if not text:
        return ""
    
    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted
