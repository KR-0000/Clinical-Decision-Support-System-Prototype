"""
Tests for FastAPI endpoints in app/routers/jobs.py.

Uses the `client` fixture from conftest.py which provides:
  - In-memory SQLite DB
  - process_case.delay mocked
  - upload_file mocked
"""

import io
import pytest
from app.models.job import JobStatus


SHORT_CASE = "65yo male chest pain"   # too short (<20 chars not meaningful — use one <20)
VALID_CASE = (
    "65-year-old male with sudden onset crushing chest pain radiating to left arm, "
    "diaphoresis, nausea, BP 160/95, HR 108. History of hypertension and type 2 diabetes."
)
TOO_SHORT_CASE = "chest pain"  # 10 chars, below 20-char minimum


# ── /health ───────────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── POST /jobs/upload — text input ────────────────────────────────────────────

def test_upload_text_returns_job_id(client):
    r = client.post("/jobs/upload", data={"case_text": VALID_CASE})
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    assert body["status"] == "pending"
    assert body["input_type"] == "text"


def test_upload_text_queues_celery_task(client):
    client.post("/jobs/upload", data={"case_text": VALID_CASE})
    client.mock_task.delay.assert_called_once()
    call_kwargs = client.mock_task.delay.call_args.kwargs
    assert call_kwargs["input_type"] == "text"
    assert call_kwargs["case_text"] == VALID_CASE


def test_upload_text_too_short_returns_400(client):
    r = client.post("/jobs/upload", data={"case_text": TOO_SHORT_CASE})
    assert r.status_code == 400
    assert "too short" in r.json()["detail"].lower()


def test_upload_no_input_returns_400(client):
    r = client.post("/jobs/upload", data={})
    assert r.status_code == 400


# ── POST /jobs/upload — PDF input ─────────────────────────────────────────────

def test_upload_pdf_returns_job_id(client):
    pdf_bytes = b"%PDF-1.4 fake pdf content for testing"
    r = client.post(
        "/jobs/upload",
        files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    assert body["input_type"] == "pdf"


def test_upload_pdf_calls_upload_file(client):
    pdf_bytes = b"%PDF-1.4 fake"
    client.post(
        "/jobs/upload",
        files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    client.mock_upload.assert_called_once()


def test_upload_pdf_queues_celery_task_with_file_ref(client):
    pdf_bytes = b"%PDF-1.4 fake"
    client.post(
        "/jobs/upload",
        files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    call_kwargs = client.mock_task.delay.call_args.kwargs
    assert call_kwargs["input_type"] == "pdf"
    assert call_kwargs["file_ref"] == "mock-job-id/file.pdf"


def test_upload_non_pdf_file_returns_400(client):
    r = client.post(
        "/jobs/upload",
        files={"file": ("notes.txt", io.BytesIO(b"plain text"), "text/plain")},
    )
    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]


def test_upload_oversized_pdf_returns_413(client):
    big_pdf = b"x" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
    r = client.post(
        "/jobs/upload",
        files={"file": ("huge.pdf", io.BytesIO(big_pdf), "application/pdf")},
    )
    assert r.status_code == 413
    assert "10 MB" in r.json()["detail"]


# ── GET /jobs/status ──────────────────────────────────────────────────────────

def test_get_status_returns_pending_after_upload(client):
    r_upload = client.post("/jobs/upload", data={"case_text": VALID_CASE})
    job_id = r_upload.json()["job_id"]

    r_status = client.get(f"/jobs/status/{job_id}")
    assert r_status.status_code == 200
    body = r_status.json()
    assert body["job_id"] == job_id
    assert body["status"] == "pending"


def test_get_status_returns_404_for_unknown_job(client):
    r = client.get("/jobs/status/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_get_status_response_includes_created_at(client):
    r_upload = client.post("/jobs/upload", data={"case_text": VALID_CASE})
    job_id = r_upload.json()["job_id"]
    r_status = client.get(f"/jobs/status/{job_id}")
    assert "created_at" in r_status.json()


# ── GET /jobs/result ──────────────────────────────────────────────────────────

def test_get_result_returns_pending_status_when_not_done(client, test_engine):
    from sqlalchemy.orm import sessionmaker
    from app.models.job import Job

    r_upload = client.post("/jobs/upload", data={"case_text": VALID_CASE})
    job_id = r_upload.json()["job_id"]

    r_result = client.get(f"/jobs/result/{job_id}")
    assert r_result.status_code == 200
    body = r_result.json()
    assert body["status"] == "pending"
    assert body["result"] is None


def test_get_result_returns_result_when_done(client, test_engine):
    from sqlalchemy.orm import sessionmaker
    from app.models.job import Job

    r_upload = client.post("/jobs/upload", data={"case_text": VALID_CASE})
    job_id = r_upload.json()["job_id"]

    # Manually advance the job to done with a fake result
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    with Session() as s:
        job = s.query(Job).filter(Job.job_id == job_id).first()
        job.status = JobStatus.done
        job.result = {"urgency": "Emergent", "patient_summary": "test"}
        s.commit()

    r_result = client.get(f"/jobs/result/{job_id}")
    assert r_result.status_code == 200
    body = r_result.json()
    assert body["status"] == "done"
    assert body["result"]["urgency"] == "Emergent"


def test_get_result_returns_error_message_when_failed(client, test_engine):
    from sqlalchemy.orm import sessionmaker
    from app.models.job import Job

    r_upload = client.post("/jobs/upload", data={"case_text": VALID_CASE})
    job_id = r_upload.json()["job_id"]

    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    with Session() as s:
        job = s.query(Job).filter(Job.job_id == job_id).first()
        job.status = JobStatus.failed
        job.error_message = "Non-retryable error: AIResponseValidationError"
        s.commit()

    r_result = client.get(f"/jobs/result/{job_id}")
    assert r_result.status_code == 200
    body = r_result.json()
    assert body["status"] == "failed"
    assert "AIResponseValidationError" in body["error_message"]
    assert body["result"] is None


def test_get_result_returns_404_for_unknown_job(client):
    r = client.get("/jobs/result/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
