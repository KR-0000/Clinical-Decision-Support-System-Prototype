"""
Tests for app/services/terminology.py.

urllib.request.urlopen is mocked — no real NLM network calls.
The key contract: verify_icd10 NEVER raises; it always returns a dict with a
'verified' key. Failed lookups return verified=False and do not crash the job.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.terminology import verify_icd10, enrich_conditions_with_verified_icd10


def _mock_nlm_response(total, results):
    """Build a mock urllib response matching the NLM API wire format.

    NLM format: [total_count, code_list, {}, [[code, name], ...]]
    """
    payload = [total, [r[0] for r in results], {}, results]
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ── verify_icd10: success paths ───────────────────────────────────────────────

def test_verify_icd10_returns_code_and_description_on_match():
    mock_resp = _mock_nlm_response(3, [["I60.9", "Nontraumatic subarachnoid hemorrhage, unspecified"]])
    with patch("app.services.terminology.urllib.request.urlopen", return_value=mock_resp):
        result = verify_icd10("Subarachnoid Hemorrhage")
    assert result["verified"] is True
    assert result["code"] == "I60.9"
    assert "subarachnoid" in result["description"].lower()


def test_verify_icd10_uses_top_result_only():
    mock_resp = _mock_nlm_response(2, [
        ["I60.9", "Nontraumatic SAH, unspecified"],
        ["I60.0", "SAH from carotid siphon"],
    ])
    with patch("app.services.terminology.urllib.request.urlopen", return_value=mock_resp):
        result = verify_icd10("Subarachnoid Hemorrhage")
    assert result["code"] == "I60.9"


def test_verify_icd10_returns_verified_false_when_no_results():
    mock_resp = _mock_nlm_response(0, [])
    with patch("app.services.terminology.urllib.request.urlopen", return_value=mock_resp):
        result = verify_icd10("Fictional Syndrome XYZ")
    assert result["verified"] is False
    assert "code" not in result


# ── verify_icd10: failure paths (must never raise) ────────────────────────────

def test_verify_icd10_returns_false_on_network_error():
    with patch("app.services.terminology.urllib.request.urlopen",
               side_effect=Exception("connection refused")):
        result = verify_icd10("Pneumonia")
    assert result["verified"] is False


def test_verify_icd10_returns_false_on_timeout():
    import urllib.error
    with patch("app.services.terminology.urllib.request.urlopen",
               side_effect=urllib.error.URLError("timed out")):
        result = verify_icd10("Pneumonia")
    assert result["verified"] is False


def test_verify_icd10_returns_false_on_malformed_response_too_short():
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps([1, []]).encode()  # only 2 elements, need 4
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("app.services.terminology.urllib.request.urlopen", return_value=mock_resp):
        result = verify_icd10("Stroke")
    assert result["verified"] is False


def test_verify_icd10_returns_false_on_invalid_json():
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"not json at all"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("app.services.terminology.urllib.request.urlopen", return_value=mock_resp):
        result = verify_icd10("Stroke")
    assert result["verified"] is False


def test_verify_icd10_never_raises_on_any_exception():
    with patch("app.services.terminology.urllib.request.urlopen",
               side_effect=RuntimeError("unexpected failure")):
        result = verify_icd10("Any Condition")
    assert "verified" in result
    assert result["verified"] is False


# ── enrich_conditions_with_verified_icd10 ────────────────────────────────────

def test_enrich_adds_verified_fields_to_each_condition():
    conditions = [
        {"condition": "Subarachnoid Hemorrhage", "icd10": "I60.9", "likelihood": "High", "reasoning": "..."},
        {"condition": "Migraine", "icd10": "G43.909", "likelihood": "Low", "reasoning": "..."},
    ]
    nlm_hit = _mock_nlm_response(1, [["I60.9", "Nontraumatic SAH"]])
    nlm_miss = _mock_nlm_response(0, [])

    with patch("app.services.terminology.urllib.request.urlopen",
               side_effect=[nlm_hit, nlm_miss]):
        enriched = enrich_conditions_with_verified_icd10(conditions)

    assert enriched[0]["icd10_verified"] is True
    assert enriched[0]["icd10_description"] == "Nontraumatic SAH"
    assert enriched[1]["icd10_verified"] is False
    assert enriched[1]["icd10_description"] is None


def test_enrich_does_not_mutate_original_conditions():
    original = [
        {"condition": "Stroke", "icd10": "I63.9", "likelihood": "High", "reasoning": "..."}
    ]
    original_copy = [dict(c) for c in original]

    with patch("app.services.terminology.urllib.request.urlopen",
               side_effect=Exception("network down")):
        enrich_conditions_with_verified_icd10(original)

    assert original == original_copy


def test_enrich_keeps_groq_code_when_unverified():
    conditions = [
        {"condition": "Unknown Syndrome", "icd10": "X99.9", "likelihood": "Low", "reasoning": "..."}
    ]
    with patch("app.services.terminology.urllib.request.urlopen",
               side_effect=Exception("NLM unreachable")):
        enriched = enrich_conditions_with_verified_icd10(conditions)

    assert enriched[0]["icd10"] == "X99.9"
    assert enriched[0]["icd10_verified"] is False


def test_enrich_returns_empty_list_for_empty_input():
    result = enrich_conditions_with_verified_icd10([])
    assert result == []
