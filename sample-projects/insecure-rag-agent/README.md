# Insecure GenAI RAG Agent Sample

This project is a safe, benign academic benchmark containing intentionally insecure patterns to verify automated static analysis and compliance crosswalk detection.

## Expected Scanner Detections

| Vulnerability | File | Rule ID | OWASP GenAI | NIST AI RMF | MITRE ATLAS | EU AI Act |
|---|---|---|---|---|---|---|
| Hardcoded Mock API Key | `app.py:10` | `RULE-KEY-OPENAI` | LLM02 | MEASURE-2.7 | AML.T0025 | Article 10 |
| F-String Prompt Injection | `app.py:15` | `FINDING-PI-FSTR` | LLM01 | MEASURE-2.5 | AML.T0051 | Article 15 |
| Insecure Output Handling (`eval`) | `app.py:21` | `FINDING-IOH` | LLM05 | MANAGE-1.3 | - | Article 15 |
| Excessive Agency (Shell Tool) | `app.py:27` | `FINDING-AGENCY` | LLM06 | GOVERN-1.2 | - | Article 14 |
| Insecure Deserialization (`pickle.load`) | `app.py:32` | `FINDING-DESER` | LLM03 | MAP-1.5 | AML.T0040 | Article 15 |
| Debug Enabled in Config | `config.yaml:4` | `CONFIG-DEBUG` | LLM02 | - | - | Article 10 |

## Expected Risk Assessment Result
- **Overall Risk Score:** >= 75 / 100
- **Risk Level:** CRITICAL
- **Compliance Status:** Multiple controls flagged as `MISSING_WITH_EVIDENCE`.
