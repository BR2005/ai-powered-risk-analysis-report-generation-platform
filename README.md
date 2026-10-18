# Lucifer: AI-Powered GenAI Security Risk & Compliance Assessment Platform

> **Academic Disclaimer:** This platform is an independent academic implementation inspired by the mapping concept of the **OWASP GenAI Security Project Crosswalk**. It does not claim official OWASP, NIST, ISO, or European Union affiliation, endorsement, or certification. Generated risk reports and compliance matrices serve as technical audit assistance aids, not substitutes for qualified legal counsel or formal security certification.

---

## 1. Project Overview

**Lucifer** is a full-stack, modular cybersecurity platform that accepts a GenAI application's source code (ZIP archive, Python/JS/TS files), architecture configuration, or documentation and performs automated, evidence-grounded security risk and compliance gap analysis.

### Core Capabilities
- **Gemma 4 Autonomous Multi-Agent Supervision:**
  - Uses Google DeepMind's configured **Gemma 4** model as the autonomous routing supervisor.
  - Dynamic conditional routing: Gemma 4 inspects real-time assessment findings, severity levels, and evidence verification status to decide which specialist agent runs next instead of following a fixed linear sequence.
  - Bounded feedback loops: The supervisor can request additional security checks or deeper evidence verification passes when high or critical vulnerabilities are discovered.
  - Safety & Guardrails: Model output validation, strict tool allowlist enforcement (`ALLOWED_AGENT_TOOLS`), prevention of arbitrary code execution, and hard execution caps (`MAX_SUPERVISOR_ITERATIONS = 10`, `MAX_EXTRA_SECURITY_LOOPS = 2`).
  - Deterministic priority-queue guardrail: Seamlessly steps in if the model is offline or unreachable.
- **Static Security Analysis:** AST-level and signature-based detection for GenAI risks:
  - Direct and indirect **Prompt Injection** (F-strings, unsanitized concatenation)
  - **Sensitive Information Disclosure** and hardcoded API keys (with automated redaction)
  - **Insecure Output Handling** (`eval()`, `exec()`, raw SQL execution from LLM completions, XSS sinks)
  - **Excessive Agency** (unrestricted OS shell/subprocess commands in agent tools)
  - **Insecure Deserialization & Supply Chain** (`pickle.load()`, `torch.load` without `weights_only=True`)
  - **Vector Store & RAG Weaknesses** (missing tenant isolation metadata filters)
- **7-Stage Specialized AI Agents Orchestrated Autonomously:**
  1. *Reconnaissance Agent:* Identifies models, vector stores, tools, and trust boundaries.
  2. *Security Analysis Agent:* Executes static code and configuration scans.
  3. *Evidence Validation Agent:* Validates file evidence, line numbers, and sanitizes snippets.
  4. *Risk Assessment Agent:* Calculates deterministic, transparent risk scores (0–100) and severity levels.
  5. *Compliance Mapping Agent:* Maps findings to crosswalk frameworks and classifies control implementation status.
  6. *Remediation Agent:* Generates prioritized mitigation steps with code diff recommendations.
  7. *Report Generation Agent:* Assembles structured JSON reports and executive PDF audit artifacts.
- **Full Crosswalk Framework Coverage:**
  - **OWASP GenAI Top 10** (LLM01–LLM10)
  - **NIST AI RMF 1.0** (Govern, Map, Measure, Manage)
  - **MITRE ATLAS** (AML.T0051, AML.T0054, AML.T0043, AML.T0025, AML.T0040)
  - **ISO/IEC 42001:2023** (AI Management Systems)
  - **ISO/IEC 23894:2023** (AI Risk Management Guidance)
  - **EU AI Act** (Articles 9, 10, 13, 14, 15, 50)
- **Dual Runtime Support:** Operates 100% out of the box with deterministic safety guardrails without requiring paid API keys or external services, with optional pluggable support for Gemma 4 via Google AI Studio, local Ollama, or OpenAI-compatible endpoints.

---

## 2. Architecture & Directory Structure

```text
genai-security-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/             # Endpoints: /health, /frameworks, /assessments, /findings, /report.pdf
│   │   ├── agents/             # Gemma 4 Supervisor, MultiAgentOrchestrator, 7 Specialist Agents, State
│   │   ├── engine/             # AST Scanner, Config Analyzer, Scoring Engine, Crosswalk Mapper
│   │   ├── models/             # SQLAlchemy ORM models (agent execution log & supervisor iterations)
│   │   ├── schemas/            # Pydantic v2 schemas
│   │   └── utils/              # Zip-slip protected safe extraction, ReportLab PDF generator
│   ├── tests/                  # 15 automated pytest suites (including multi-agent supervisor tests)
│   ├── Dockerfile              # Backend container definition
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # Type-safe Axios API client
│   │   ├── components/         # AgentExecutionTrace, PipelineTimeline, SeverityBadge, RiskScoreGauge, Modal
│   │   ├── pages/              # Dashboard, NewAssessment, AssessmentDetails, Findings, Compliance, Reports
│   │   └── types/              # TypeScript interfaces (SupervisorDecision, AgentExecutionRecord)
│   ├── Dockerfile              # Multi-stage Nginx container
│   └── package.json            # React 19, Vite, Tailwind CSS v4, React Router, Recharts
├── compliance-rules/           # Versioned JSON control catalogs and crosswalk mappings
│   ├── schema.json             # JSON Schema for control definitions
│   ├── frameworks.json         # Frameworks registry
│   ├── owasp_genai_top10.json
│   ├── nist_ai_rmf.json
│   ├── mitre_atlas.json
│   ├── iso_42001.json
│   ├── iso_23894.json
│   ├── eu_ai_act.json
│   └── crosswalk_mappings.json # Evidence-grounded risk-to-control crosswalk
├── sample-projects/            # Harmless static benchmark examples
│   ├── insecure-rag-agent/     # Triggers detectable vulnerabilities (Score >= 75)
│   └── secure-rag-agent/       # Mitigated implementation (Score = 0.0)
├── docker-compose.yml          # Multi-container orchestration (Backend + Frontend + pgvector)
└── README.md
```

---

## 3. Quick Start (Windows PowerShell)

### Prerequisites
- Python 3.11+
- Node.js v20+ & npm

### Step 1: Start the Backend
Open a PowerShell terminal:
```powershell
# Navigate to backend directory
cd "d:\ai powered risk analysis report generation platform\backend"

# Copy .env.example to .env and set a unique API_ACCESS_KEY before running.
# Replace the placeholder model credentials if using a hosted model.

# Activate existing virtual environment
.\.venv\Scripts\Activate.ps1

# Run the FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --env-file .env
```
The backend API is now live at `http://127.0.0.1:8000`.
- Health Check: `http://127.0.0.1:8000/health`
- Interactive Swagger API Docs: `http://127.0.0.1:8000/docs`

### Step 2: Start the Frontend
Open a second PowerShell terminal:
```powershell
# Navigate to frontend directory
cd "d:\ai powered risk analysis report generation platform\frontend"

# Launch Vite development server
npm run dev
```
Open your browser to `http://localhost:5173`.

---

## 4. Docker Compose Setup

Copy the root `.env.example` to `.env` and replace both secrets before starting the stack:

```env
API_ACCESS_KEY=replace_with_a_long_random_secret
POSTGRES_PASSWORD=replace_with_a_long_url_safe_random_secret
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.example
```

The key protects assessment, finding, and report endpoints. The frontend prompts for it and retains it only in the current browser tab. This is a shared-key setup: every key holder can access all stored assessments, so use it only for a trusted group and use HTTPS. Framework metadata and the health endpoint remain public.

To launch the full stack (FastAPI Backend, React Nginx Frontend, and PostgreSQL with pgvector):

```powershell
# In project root
docker compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API: `http://127.0.0.1:8000` (bound to localhost)
- Swagger Docs: `http://localhost:8000/docs`
- Access protected API routes with `X-API-Key: <API_ACCESS_KEY>`.
- PostgreSQL is available only to services on the internal Docker network.

---

## 5. Running Automated Tests

Run the full automated test suite to verify the autonomous Gemma 4 multi-agent supervisor, confirmed finding flows, bounded feedback loops, termination limits, tool allowlists, AST scanners, upload security, and PDF report generation:

```powershell
cd "d:\ai powered risk analysis report generation platform\backend"
.\.venv\Scripts\Activate.ps1

# Run all backend tests
pytest -v

# Run dedicated multi-agent autonomous supervisor tests
pytest app/tests/test_multi_agent_supervisor.py -v
```

To run frontend production bundle verification:
```powershell
cd "d:\ai powered risk analysis report generation platform\frontend"
npm run build
```

---

## 6. Testing with Sample Projects

The workspace includes benign static sample projects in `sample-projects/`:

1. **Insecure RAG Agent (`sample-projects/insecure-rag-agent/`):**
   - Contains direct prompt injection via f-strings, `eval()` output execution, hardcoded dummy key, unconstrained subprocess tool, and pickle loading.
   - Run assessment via the UI or API: triggers autonomous detection, evidence validation loop, yields **CRITICAL** risk score (>= 75/100), and records the Gemma 4 supervisor decision trail.
2. **Secure RAG Agent (`sample-projects/secure-rag-agent/`):**
   - Implements role-isolated prompt templates, Pydantic schema validation, environment variables for secrets, command whitelisting, and safe JSON serialization.
   - Run assessment via the UI: yields **0.0 / 100** risk score and **0 vulnerabilities**.

---

## 7. Gemma 4 Model Configuration

The platform operates **100% out-of-the-box with safety guardrails** without requiring API keys. To connect the autonomous supervisor to Gemma 4:

Edit `backend/.env`:

### Option A: Google AI Studio (Official Gemma 4 Endpoint)
```env
LLM_PROVIDER=google-ai-studio
GEMMA_MODEL=gemma-4-12b-it
GEMMA_API_KEY=AIzaSy...
```

### Option B: Local Ollama (Local Gemma 4 Runtime)
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma-4
```

### Option C: OpenAI-Compatible Server (vLLM / LM Studio / OpenRouter serving Gemma 4)
```env
LLM_PROVIDER=openai-compatible
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gemma-4-12b-it
```

*Note: Gemma 4 autonomously controls agent routing, additional investigation loops, and report generation. Authoritative risk scores, evidence snippet extraction, and compliance control status determinations are verified through deterministic ground-truth engines.*

---

## 8. API Specification

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and database connectivity |
| `GET` | `/api/v1/frameworks` | Supported frameworks, controls catalog, and source URLs |
| `POST` | `/api/v1/assessments` | Manual architecture description assessment |
| `POST` | `/api/v1/assessments/upload` | Secure ZIP/code file upload with Zip-slip defense |
| `GET` | `/api/v1/assessments` | List historical assessments |
| `GET` | `/api/v1/assessments/{id}` | Detailed assessment findings, scores, and control mappings |
| `GET` | `/api/v1/assessments/{id}/report` | Structured JSON audit report |
| `GET` | `/api/v1/assessments/{id}/report.pdf` | Downloadable executive PDF audit report |
| `GET` | `/api/v1/findings` | Filter findings by severity, category, status, or assessment |
