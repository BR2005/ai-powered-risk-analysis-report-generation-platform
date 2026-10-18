# Secure GenAI RAG Agent Sample

This project demonstrates hardened, compliant GenAI patterns that successfully mitigate security vulnerabilities.

## Implemented Security Controls

1. **Prompt Injection Defense (OWASP LLM01 / NIST MEASURE-2.5):**
   - User inputs sanitized and bounded.
   - Distinct system/user role separation; no dynamic string interpolation into system instructions.

2. **Sensitive Information Disclosure (OWASP LLM02 / NIST MEASURE-2.7):**
   - No hardcoded API keys; secrets loaded strictly from environment variables.

3. **Insecure Output Handling (OWASP LLM05 / EU AI Act Art 15):**
   - Zero dynamic `eval()` or `exec()`.
   - Structured JSON validation enforced via Pydantic model schemas.

4. **Excessive Agency Defense (OWASP LLM06 / EU AI Act Art 14):**
   - Strict command whitelisting.
   - Mandatory human-in-the-loop (HITL) approval gate before state modification.

5. **Supply Chain Security (OWASP LLM03 / MITRE AML.T0040):**
   - Standard JSON serialization instead of unsafe Python `pickle` unpickling.

## Expected Risk Assessment Result
- **Overall Risk Score:** 0.0 / 100
- **Risk Level:** INFORMATIONAL
- **Vulnerabilities Detected:** 0
