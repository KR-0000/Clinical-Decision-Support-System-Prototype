# Technical guide

[Project overview](../README.md)

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

When a visitor requests live analysis, the frontend wakes the API and worker concurrently through readable `/health` requests, then submits the case once. The preparation screen explains the delay and offers recovery if startup times out. Opening the worker manually is a fallback rather than a prerequisite.

The API response is `{"status":"ok"}`; the worker response is `{"http_service":"awake"}`. These confirm HTTP startup, not database, Redis, Groq or Celery readiness. A job reaching `processing` confirms that Celery picked it up. The worker root URL still returns `worker alive` for manual checks.

The eight example-case buttons prefill editable clinical narratives. **How it works** opens a separate, simulated walkthrough with a visible cursor, step progress, pause/next/exit controls and an input-first demonstration. It makes no clinical API requests and restores the visitor's draft on exit. Actual analysis is explicitly requested through submission.

### Troubleshooting failed submissions

`Error: Failed to fetch` is a browser network/CORS error, not evidence of a bad Groq key. An unhandled API exception can produce a response without CORS headers, hiding the actual server failure from the frontend. Database and queue failures now return readable HTTP 503 errors. Database connections are checked before reuse to recover from stale idle connections.

1. Open the API `/health` URL and wait for its cold start. This endpoint confirms the API process is alive; it does **not** check Postgres, Redis, or Groq. Check the Render API logs at the time of a failed request.
2. If a database error appears, check that the Supabase project is active and that `DATABASE_URL` is current in **both** Render services. Free Supabase projects can pause after inactivity. Restore a paused project in Supabase before retrying.
3. If a queue error appears, check the Upstash database status, limits, and TLS Redis connection URL. `REDIS_URL` must match in the API and worker. The local `.env` does not update Render environment variables.
4. If submission succeeds but stays `pending`, open the worker URL, then check **Celery's logs** for a successful Redis connection and task receipt. `worker alive` only confirms the separate HTTP health server is running; it does not prove Celery is consuming jobs.
5. If a job fails during analysis, inspect the worker logs. A Groq 401 calls for replacing `GROQ_API_KEY` in the worker environment; a 429 calls for checking limits. Confirm model availability before changing models. The configured model is `openai/gpt-oss-120b`.
6. For CORS errors, set `ALLOWED_ORIGINS` in both API and worker to the exact frontend origin (no trailing slash). For local browser development, include the actual local frontend origin, such as `http://127.0.0.1:8766`, in the comma-separated allowlist. Do not put API keys in frontend HTML.

After updating environment variables, redeploy/restart the affected Render services. After deploying code changes, redeploy the API and worker Docker services and publish the frontend. The Docker image uses Python 3.13 to match `pyproject.toml` and `uv.lock`, and installs frozen production dependencies.

The interface and startup changes require no new API keys. Keep the existing Groq key in the worker environment; rotate it only if revoked, exposed or rejected with an authentication error. A successful local commit/push does not by itself prove Render has finished deploying all three services. Verify a synthetic text case and a text-based PDF after deployment, including a cold start with no worker tab open.

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

The Python suite covers API endpoints, clinical fixtures, AI response validation, PDF extraction, terminology lookup, retry behavior, worker tasks, startup health and input limits. External clinical services are mocked. A worker-health test uses a local HTTP server.

The frontend runtime suite covers startup, submission deduplication, error recovery, example inputs, result rendering and walkthrough isolation.

```bash
node --test tests/frontend_runtime.cjs
```

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
├── Dockerfile                   # python:3.13-slim, non-root appuser
├── docker-compose.yml           # Redis + API + Worker for local dev
├── render.yaml                  # Render Blueprint (all three services)
├── worker_health.py             # Minimal HTTP server for Render port binding
├── start_worker.sh              # Starts worker_health.py + Celery
└── pyproject.toml               # uv-managed; dev deps in [dependency-groups].dev
```
---

## Future Improvements

Potential next steps include:
- Evaluating system performance with larger clinical datasets
- Improving retrieval and validation methods for medical information
- Adding additional safety checks and clinician feedback workflows
- Expanding deployment and monitoring capabilities

---

## Contribution

This project was independently designed and developed, including backend architecture, API development, AI integration, database design, testing, and deployment.

---

## Disclaimer

This tool is a prototype intended to assist clinical reasoning. It is not a medical device, has not undergone clinical validation, and must not be used as a substitute for professional medical judgment. Always verify AI-generated output against established clinical guidelines and your own assessment.
