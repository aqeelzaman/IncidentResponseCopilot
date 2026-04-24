# Incident Response Copilot

AI-powered production incident triage system. A user describes a production symptom;
a LangGraph supervisor orchestrates four specialist agents in parallel and returns a
ranked root-cause hypothesis with a step-by-step fix plan — all within ~90 seconds.

## Architecture

```
User → Next.js UI → FastAPI (SSE) → LangGraph Supervisor
                                          ├── Log Analyst      → BigQuery
                                          ├── Runbook RAG      → Pinecone (runbooks)
                                          ├── Incident History → Pinecone (incidents)
                                          └── Remediation      → GPT-4o (self-reflection)
```

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 App Router · TypeScript · Tailwind CSS |
| Backend | Python 3.11 · FastAPI · Uvicorn · SSE streaming |
| Agents | LangGraph (supervisor pattern) · LangChain ReAct |
| LLM | OpenAI GPT-4o |
| Vector DB | Pinecone (`runbooks` + `incidents` indexes) |
| Data | BigQuery (`incident_copilot` dataset) |
| Infra | Terraform · Cloud Run · Secret Manager |
| Observability | `trace_id` threaded through every agent call |

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- Pinecone API key
- GCP project with BigQuery enabled (for full functionality)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys

# Seed data (requires GCP + Pinecone credentials)
python data/seed_bigquery.py
python data/seed_pinecone.py

# Run backend
python main.py
# → http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install

cp .env.example .env.local
# Set BACKEND_URL=http://localhost:8000

npm run dev
# → http://localhost:3000
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

## Demo Scenario

**Input:**
> checkout-service is returning 503s, orders are failing, started about 90 minutes ago

**Expected output:**
- **Log Analyst:** 847 ERROR logs + `p99_latency = 4.2s` in BigQuery
- **Runbook RAG:** "DB Connection Pool Exhaustion" — increase `pool_size` from 10→50
- **Incident History:** 2 similar past incidents (both DB pool exhaustion)
- **Remediation:** Root cause: DB connection pool exhausted (confidence: 0.91). Immediate: patch ConfigMap, restart pod. Follow-up: add pool monitoring alert.

## GCP Deployment

### 1. Build and push the backend image

```bash
gcloud auth configure-docker
docker build -t gcr.io/<PROJECT>/incident-copilot:latest backend/
docker push gcr.io/<PROJECT>/incident-copilot:latest
```

### 2. Populate secrets in Secret Manager

```bash
echo -n "sk-..." | gcloud secrets versions add openai-api-key --data-file=-
echo -n "pc-..." | gcloud secrets versions add pinecone-api-key --data-file=-
```

### 3. Apply Terraform

```bash
cd infra
terraform init
terraform apply -var="project_id=<PROJECT>" -var="backend_image=gcr.io/<PROJECT>/incident-copilot:latest"
```

### 4. Deploy frontend to Vercel or Cloud Run

Set `BACKEND_URL` env var to the Cloud Run URL from Terraform output.

## Project Structure

```
incident-copilot/
├── frontend/                  # Next.js 14 App Router UI
│   └── app/
│       ├── page.tsx           # Three-panel chat interface
│       ├── api/triage/        # SSE proxy to FastAPI
│       └── components/        # IncidentInput, ChatWindow, TriageReport
├── backend/
│   ├── main.py                # FastAPI + SSE streaming endpoint
│   ├── middleware/trace.py    # trace_id injection via ContextVar
│   ├── agents/                # LangGraph nodes + specialist agents
│   │   ├── supervisor.py      # StateGraph with parallel fan-out
│   │   ├── log_analyst.py     # ReAct agent — BigQuery tools
│   │   ├── runbook_rag.py     # ReAct agent — Pinecone runbook search
│   │   ├── incident_history.py # ReAct agent — Pinecone incident search
│   │   └── remediation.py     # 3-step self-reflection chain (no tools)
│   ├── tools/                 # LangChain @tool definitions
│   ├── data/                  # Seed scripts + 50 runbook markdown files
│   └── tests/                 # pytest with mocked LLM calls
└── infra/                     # Terraform: Cloud Run, BigQuery, Secrets, VPC
```

## Observability

Every request gets a `trace_id` (UUID) injected by `TraceMiddleware`. It is:
- Stored in `request.state.trace_id`
- Available to all agents via `contextvars.ContextVar`
- Passed as `metadata.trace_id` in every LLM call
- Returned in SSE `done` event and `X-Trace-ID` response header
- Logged to `BigQuery.trace_log` table
