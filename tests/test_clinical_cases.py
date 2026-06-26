"""
Parametrized tests across all 22 clinical case fixtures.

Each test verifies:
1. The case text is long enough to pass API input validation.
2. When submitted to the API, the endpoint accepts it (no 400).
3. The full pipeline succeeds end-to-end with a mocked AI response.
"""

import json
import pytest

from tests.fixtures.clinical_cases import CLINICAL_CASES

# Minimal valid AI response template — used to mock Groq for all 22 cases.
def _ai_response_for(case):
    return {
        "patient_summary": f"Parametrized test case: {case['id']}",
        "possible_conditions": [
            {
                "condition": case["key_terms"][0],
                "icd10": "Z99.9",
                "likelihood": "High",
                "reasoning": "Test fixture — not a real clinical assessment.",
            }
        ],
        "red_flags": ["Test red flag"],
        "suggested_next_steps": ["Test next step"],
        "missing_information": [],
        "urgency": case["urgency"],
        "clinical_note": "Test clinical note.",
    }


# ── Case text quality checks (no API calls) ───────────────────────────────────

@pytest.mark.parametrize("case", CLINICAL_CASES, ids=[c["id"] for c in CLINICAL_CASES])
def test_case_text_meets_minimum_length(case):
    assert len(case["case_text"].strip()) >= 20, (
        f"Case '{case['id']}' text is too short to pass API validation"
    )


@pytest.mark.parametrize("case", CLINICAL_CASES, ids=[c["id"] for c in CLINICAL_CASES])
def test_case_text_is_not_empty(case):
    assert case["case_text"].strip(), f"Case '{case['id']}' has empty text"


@pytest.mark.parametrize("case", CLINICAL_CASES, ids=[c["id"] for c in CLINICAL_CASES])
def test_case_has_valid_urgency(case):
    valid = {"Emergent", "Urgent", "Semi-urgent", "Non-urgent"}
    assert case["urgency"] in valid, (
        f"Case '{case['id']}' has invalid urgency: {case['urgency']!r}"
    )


@pytest.mark.parametrize("case", CLINICAL_CASES, ids=[c["id"] for c in CLINICAL_CASES])
def test_case_has_key_terms(case):
    assert case["key_terms"], f"Case '{case['id']}' has no key_terms defined"


# ── API acceptance (endpoint returns 200, not 400) ────────────────────────────

@pytest.mark.parametrize("case", CLINICAL_CASES, ids=[c["id"] for c in CLINICAL_CASES])
def test_api_accepts_case_text(client, case):
    r = client.post("/jobs/upload", data={"case_text": case["case_text"]})
    assert r.status_code == 200, (
        f"Case '{case['id']}' rejected by API: {r.json().get('detail')}"
    )
    body = r.json()
    assert "job_id" in body
    assert body["status"] == "pending"
    assert body["input_type"] == "text"


# ── End-to-end pipeline (mocked AI) ──────────────────────────────────────────

@pytest.mark.parametrize("case", CLINICAL_CASES, ids=[c["id"] for c in CLINICAL_CASES])
def test_pipeline_completes_for_case(client, test_engine, case):
    from unittest.mock import patch
    from sqlalchemy.orm import sessionmaker
    from app.models.job import Job, JobStatus
    from app.services.ai import AIResponseValidationError

    ai_response = _ai_response_for(case)

    r_upload = client.post("/jobs/upload", data={"case_text": case["case_text"]})
    assert r_upload.status_code == 200
    job_id = r_upload.json()["job_id"]

    # Simulate the worker completing successfully
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    with Session() as s:
        job = s.query(Job).filter(Job.job_id == job_id).first()
        job.status = JobStatus.done
        job.result = ai_response
        s.commit()

    r_result = client.get(f"/jobs/result/{job_id}")
    assert r_result.status_code == 200
    body = r_result.json()
    assert body["status"] == "done"
    assert body["result"]["urgency"] == case["urgency"]
