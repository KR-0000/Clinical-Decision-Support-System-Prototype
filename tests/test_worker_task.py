"""
Tests for app/workers/tasks.py — the Celery process_case task.

Uses apply() to run the task synchronously without a real broker.
All external services (DB, Groq, Supabase, NLM) are mocked.
"""

import json
import uuid
import pytest
from unittest.mock import patch, MagicMock, call
from sqlalchemy.orm import sessionmaker

from app.workers.tasks import process_case
from app.models.job import Job, JobStatus
from app.services.ai import AIResponseValidationError


VALID_AI_RESULT = {
    "patient_summary": "65yo male with chest pain.",
    "possible_conditions": [
        {
            "condition": "STEMI",
            "icd10": "I21.9",
            "likelihood": "High",
            "reasoning": "ST elevation in V1-V4.",
            "icd10_verified": True,
            "icd10_description": "Acute myocardial infarction, unspecified",
        }
    ],
    "red_flags": ["ST elevation requires immediate cath lab activation"],
    "suggested_next_steps": ["Activate STEMI protocol"],
    "missing_information": ["Troponin trend"],
    "urgency": "Emergent",
    "clinical_note": "Door-to-balloon time is the critical metric.",
}


def _run_task(job_id, input_type, case_text=None, file_ref=None):
    """Run process_case synchronously via apply()."""
    return process_case.apply(kwargs={
        "job_id": job_id,
        "input_type": input_type,
        "case_text": case_text,
        "file_ref": file_ref,
    })


# ── Success: text input ───────────────────────────────────────────────────────

def test_text_job_marked_done_on_success(db_session):
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, input_type="text", status=JobStatus.pending)
    db_session.add(job)
    db_session.commit()

    Session = MagicMock(return_value=db_session)

    with patch("app.services.database.SessionLocal", Session), \
         patch("app.services.ai.analyze_case", return_value=VALID_AI_RESULT), \
         patch("app.services.terminology.enrich_conditions_with_verified_icd10",
               return_value=VALID_AI_RESULT["possible_conditions"]):
        _run_task(job_id, "text", case_text="65yo male with crushing chest pain, ST elevation.")

    final_job = db_session.query(Job).filter(Job.job_id == job_id).first()
    assert final_job.status == JobStatus.done
    assert final_job.result is not None
    assert final_job.result["urgency"] == "Emergent"


def test_text_job_passes_case_text_to_analyze_case(db_session):
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, input_type="text", status=JobStatus.pending)
    db_session.add(job)
    db_session.commit()

    captured_texts = []

    def capture_analyze(text):
        captured_texts.append(text)
        return VALID_AI_RESULT

    Session = MagicMock(return_value=db_session)
    with patch("app.services.database.SessionLocal", Session), \
         patch("app.services.ai.analyze_case", side_effect=capture_analyze), \
         patch("app.services.terminology.enrich_conditions_with_verified_icd10",
               return_value=VALID_AI_RESULT["possible_conditions"]):
        _run_task(job_id, "text", case_text="specific case description here")

    assert captured_texts[0] == "specific case description here"


# ── Success: PDF input ────────────────────────────────────────────────────────

def test_pdf_job_downloads_and_extracts_before_analysis(db_session):
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, input_type="pdf", status=JobStatus.pending)
    db_session.add(job)
    db_session.commit()

    Session = MagicMock(return_value=db_session)
    with patch("app.services.database.SessionLocal", Session), \
         patch("app.services.storage.download_file", return_value=b"fake pdf bytes") as mock_dl, \
         patch("app.services.pdf_extractor.extract_text", return_value="extracted clinical text") as mock_ext, \
         patch("app.services.ai.analyze_case", return_value=VALID_AI_RESULT), \
         patch("app.services.terminology.enrich_conditions_with_verified_icd10",
               return_value=VALID_AI_RESULT["possible_conditions"]):
        _run_task(job_id, "pdf", file_ref="mock-job-id/report.pdf")

    mock_dl.assert_called_once_with("mock-job-id/report.pdf")
    mock_ext.assert_called_once_with(b"fake pdf bytes")

    final_job = db_session.query(Job).filter(Job.job_id == job_id).first()
    assert final_job.status == JobStatus.done


# ── Non-retryable failure ─────────────────────────────────────────────────────

def test_non_retryable_error_marks_job_failed_immediately(db_session):
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, input_type="text", status=JobStatus.pending)
    db_session.add(job)
    db_session.commit()

    Session = MagicMock(return_value=db_session)
    with patch("app.services.database.SessionLocal", Session), \
         patch("app.services.ai.analyze_case",
               side_effect=AIResponseValidationError("missing field: urgency")):
        _run_task(job_id, "text", case_text="some case text here to analyze")

    # The task closes the session in its finally block, so re-query by ID.
    final_job = db_session.query(Job).filter(Job.job_id == job_id).first()
    assert final_job.status == JobStatus.failed
    assert "urgency" in final_job.error_message


def test_scanned_pdf_marks_job_failed_immediately(db_session):
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, input_type="pdf", status=JobStatus.pending)
    db_session.add(job)
    db_session.commit()

    Session = MagicMock(return_value=db_session)
    with patch("app.services.database.SessionLocal", Session), \
         patch("app.services.storage.download_file", return_value=b"scanned pdf"), \
         patch("app.services.pdf_extractor.extract_text",
               side_effect=ValueError("No readable text found in this PDF")):
        _run_task(job_id, "pdf", file_ref="job/scan.pdf")

    final_job = db_session.query(Job).filter(Job.job_id == job_id).first()
    assert final_job.status == JobStatus.failed
    assert "No readable text" in final_job.error_message


# ── Missing job record ────────────────────────────────────────────────────────

def test_missing_job_record_does_not_crash(db_session):
    Session = MagicMock(return_value=db_session)
    with patch("app.services.database.SessionLocal", Session):
        result = _run_task("nonexistent-job-id", "text", case_text="some text here")
    # Task should complete without raising an exception
    assert result is not None


# ── ICD-10 enrichment is called ───────────────────────────────────────────────

def test_icd10_enrichment_is_applied_to_result(db_session):
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, input_type="text", status=JobStatus.pending)
    db_session.add(job)
    db_session.commit()

    enriched_conditions = [{
        **VALID_AI_RESULT["possible_conditions"][0],
        "icd10_verified": True,
        "icd10_description": "Verified by NLM",
    }]

    Session = MagicMock(return_value=db_session)
    with patch("app.services.database.SessionLocal", Session), \
         patch("app.services.ai.analyze_case", return_value=VALID_AI_RESULT), \
         patch("app.services.terminology.enrich_conditions_with_verified_icd10",
               return_value=enriched_conditions) as mock_enrich:
        _run_task(job_id, "text", case_text="clinical case text for analysis")

    mock_enrich.assert_called_once()
    final_job = db_session.query(Job).filter(Job.job_id == job_id).first()
    assert final_job.result["possible_conditions"][0]["icd10_description"] == "Verified by NLM"
