# Clinical Decision Support System (Prototype)

A decision support tool for clinicians. Submit a patient case as free-text or a PDF clinical summary and receive a structured differential with possible conditions, ICD-10 codes, red flags, and suggested next steps.

## Background and motivation

Consider a common care transition scenario: a patient visits their primary care physician, who determines they need hospital-level care. The physician writes a referral and prepares a clinical summary documenting the patient's history, current medications, vitals, and preliminary findings. When the patient arrives at the hospital and is being admitted, the receiving clinician needs to quickly orient themselves to that documentation before deciding on a course of action.

This tool is designed for that kind of moment. A clinician can paste in a clinical summary or upload it as a PDF, and receive a structured output covering likely conditions, urgency level, red flags that may require immediate attention, and suggested next diagnostic steps. The intent is to reduce the cognitive load of synthesizing a dense referral document under time pressure, not to replace the clinician's judgment.

Healthcare systems in the US already handle care transitions at scale through EHR integrations and HL7 data exchange pipelines. This project is my attempt to prototype the core problem at a smaller scale, and to build hands-on experience with the full engineering stack involved: async task queues, LLM APIs, structured output validation, containerization, and cloud deployment. It is not production software and has not been validated clinically.

**Intended audience:** Medical professionals or developers evaluating the tool's behavior. This tool supports clinical reasoning and must not be used as a standalone diagnostic instrument.

---

## Architecture

```
  Browser / Frontend (Render Static)
        |
        | POST /jobs/upload  (multipart/form-data: text or PDF)
        v
  +-----------------------------------------+
  |           FastAPI  (cds-api)            |
  |  * validates input, enforces 10 MB cap  |
  |  * rate-limited: 10 req/min per IP      |
  |  * creates Job row -> returns job_id    |
  +----------------+------------------------+
                   |
                   | process_case.delay(job_id, ...)
                   v
  +-----------------------------------------+
  |        Upstash Redis  (rediss://)       |
  |        Celery task queue / result store |
  +----------------+------------------------+
                   |
                   | worker picks up task
                   v
  +-----------------------------------------+
  |        Celery Worker  (cds-worker)      |
  |  1. download PDF from Supabase Storage  |
  |     (if input_type == "pdf")            |
  |  2. extract text  (pdfplumber)          |
  |  3. analyze case  (Groq LLM)            |
  |  4. verify ICD-10 codes  (NLM API)      |
  |  5. write result -> Job row             |
  +------+--------------------+-------------+
         |                    |
         v                    v
  +-------------+    +--------------------+
  |  Supabase   |    |  Supabase Postgres |
  |  Storage    |    |  jobs table        |
  |  (PDF blobs)|    |  (status + result) |
  +-------------+    +--------------------+
                   ^
                   | GET /jobs/status/{job_id}
                   | GET /jobs/result/{job_id}
        Browser polls until status == "done"
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.136+ |
| Task queue | Celery 5.6+ |
| Message broker / result backend | Upstash Redis (TLS, `rediss://`) |
| Database | Supabase Postgres via SQLAlchemy 2.0 |
| File storage | Supabase Storage |
| LLM | Groq (`openai/gpt-oss-120b`) |
| PDF extraction | pdfplumber |
| ICD-10 verification | NLM ICD-10-CM API (no key required) |
| Rate limiting | slowapi (10 req/min on `/jobs/upload`) |
| Migrations | Alembic |
| Containerization | Docker (non-root `appuser`) |
| Deployment | Render free tier (Blueprint via `render.yaml`) |
| Package manager | uv |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/jobs/upload` | Submit a case (text or PDF). Returns `job_id`. |
| `GET` | `/jobs/status/{job_id}` | Poll job status: `pending` -> `processing` -> `done` / `failed` |
| `GET` | `/jobs/result/{job_id}` | Retrieve structured differential once status is `done` |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |

### Result schema

```json
{
  "patient_summary": "...",
  "possible_conditions": [
    {
      "condition": "STEMI",
      "icd10": "I21.9",
      "icd10_verified": true,
      "icd10_description": "Acute myocardial infarction, unspecified",
      "likelihood": "High",
      "reasoning": "..."
    }
  ],
  "red_flags": ["..."],
  "suggested_next_steps": ["..."],
  "missing_information": ["..."],
  "urgency": "Emergent",
  "clinical_note": "..."
}
```

`icd10_verified` indicates whether the code was confirmed against the NLM ICD-10-CM API. Groq's suggested code is preserved either way; unverified codes are flagged rather than silently dropped.

---

## Live Deployment

| Service | URL |
|---|---|
| Frontend | https://clinical-decision-support-system-1cqq.onrender.com |
| API | https://cds-api-8k33.onrender.com |
| API docs | https://cds-api-8k33.onrender.com/docs |
| Worker | https://cds-worker.onrender.com |

### Render free-tier cold start

Both the API and Worker run on Render's free plan, which spins down containers after roughly 15 minutes of inactivity. The Worker must be awake before a case submission will process.

**Before using the frontend, visit the worker URL first:**

1. Open https://cds-worker.onrender.com/ in a new tab and wait for it to return `worker alive` (up to 60 seconds on a cold start).
2. Then open the frontend and submit a case normally.

Skipping this step will cause the frontend to spin indefinitely after submission. The worker container is asleep and not consuming tasks from Redis, so submitted jobs never get picked up.

---

## Local Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/) for Python package management
- A `.env` file at the project root (copy `.env.example` and fill in values)

### Run without Docker

```bash
# Install all dependencies including the dev group
uv sync --group dev

# Run database migrations
uv run alembic upgrade head

# Terminal 1: start the API
uv run uvicorn app.main:app --reload

# Terminal 2: start the Celery worker
# Windows requires --pool=solo (no fork support)
uv run celery -A app.workers.tasks worker --loglevel=info --pool=solo
```

API: http://localhost:8000 | Docs: http://localhost:8000/docs

> **Windows / Redis:** A local Redis instance is required. [Memurai](https://www.memurai.com/) is a free Redis-compatible server for Windows. If you use Docker Compose instead, Redis is included automatically.

### Run with Docker Compose

Postgres and Supabase Storage remain on Supabase cloud. Docker Compose handles Redis, the API, and the Celery worker locally.

```bash
# Build and start all services
docker-compose up --build

# Detached mode
docker-compose up --build -d

# Tail logs for a specific service
docker-compose logs -f worker

# Stop everything
docker-compose down
```

API: http://localhost:8000

### Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase Postgres connection string |
| `REDIS_URL` | `redis://localhost:6379/0` locally; `rediss://...` for Upstash in production |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase `service_role` key (grants full DB access; keep this secret) |
| `GROQ_API_KEY` | Groq API key |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins. Omit locally (defaults to `*`). Set to the exact frontend URL in production. |

---

## Tests

```bash
uv run python -m pytest tests/ -v
```

219 tests, all passing in under 3 seconds. Zero real network calls; Groq, Supabase, NLM, and Redis are all mocked.

| File | Tests | What it covers |
|---|---|---|
| `test_ai_validation.py` | 28 | `analyze_case`, `_validate_response`: all required fields, invalid values, JSON parse failures, Groq error propagation |
| `test_retry_classification.py` | 15 | `_is_retryable()` for every Groq exception type and Celery `SoftTimeLimitExceeded` |
| `test_pdf_extraction.py` | 9 | `extract_text`: success, blank page skipping, no-text `ValueError` |
| `test_terminology.py` | 12 | NLM ICD-10-CM lookup: success, 404, network error, malformed response |
| `test_endpoints.py` | 18 | All FastAPI routes: text/PDF upload, status polling, result retrieval, error cases |
| `test_worker_task.py` | 7 | Celery `process_case` task: text/PDF paths, retryable vs non-retryable failures, ICD-10 enrichment |
| `test_clinical_cases.py` | 88 | 22 clinical fixtures x 4 parametrized checks across 10 specialties (cardiac, neurological, respiratory, sepsis, GI, obstetric, endocrine, trauma, psychiatric, dermatological) |

---

## Project Structure

```
clinical-decision-support-system-prototype/
├── app/
│   ├── main.py                  # FastAPI app, CORS, rate limit registration
│   ├── limiter.py               # shared slowapi Limiter instance
│   ├── models/job.py            # SQLAlchemy Job model + Pydantic schemas
│   ├── routers/jobs.py          # POST /jobs/upload, GET /jobs/status, GET /jobs/result
│   ├── services/
│   │   ├── ai.py                # Groq integration, response validation
│   │   ├── database.py          # SQLAlchemy engine + get_db dependency
│   │   ├── pdf_extractor.py     # pdfplumber text extraction
│   │   ├── storage.py           # Supabase Storage upload/download
│   │   └── terminology.py       # NLM ICD-10-CM verification
│   └── workers/tasks.py         # Celery app + process_case task
├── frontend/                    # Static HTML served by Render static site
│   ├── index.html
│   └── result.html
├── tests/
│   ├── conftest.py
│   ├── fixtures/clinical_cases.py
│   └── test_*.py
├── migrations/                  # Alembic migrations
├── Dockerfile                   # python:3.11-slim, non-root appuser
├── docker-compose.yml           # Redis + API + Worker for local dev
├── render.yaml                  # Render Blueprint (all three services)
├── worker_health.py             # Minimal HTTP server for Render port binding
├── start_worker.sh              # Starts worker_health.py + Celery
└── pyproject.toml               # uv-managed; dev deps in [dependency-groups].dev
```

---

## Disclaimer

This tool is a prototype intended to assist clinical reasoning. It is not a medical device, has not undergone clinical validation, and must not be used as a substitute for professional medical judgment. Always verify AI-generated output against established clinical guidelines and your own assessment.
