"""
Tests for app/services/ai.py.

Covers _validate_response (structural validation) and analyze_case (Groq integration).
No real network calls — the Groq client is mocked throughout.
"""

import json
import copy
import pytest
from unittest.mock import patch, MagicMock

from app.services.ai import analyze_case, _validate_response, AIResponseValidationError


# ── Shared valid response fixture ─────────────────────────────────────────────

VALID_RESPONSE = {
    "patient_summary": "58-year-old female presenting with thunderclap headache rated 10/10.",
    "possible_conditions": [
        {
            "condition": "Subarachnoid Hemorrhage",
            "icd10": "I60.9",
            "likelihood": "High",
            "reasoning": "Thunderclap onset with neck stiffness is the classic SAH triad.",
        },
        {
            "condition": "Migraine",
            "icd10": "G43.909",
            "likelihood": "Low",
            "reasoning": "Less likely given severity and meningeal signs.",
        },
    ],
    "red_flags": ["Thunderclap onset requires immediate non-contrast CT head"],
    "suggested_next_steps": ["Non-contrast CT head stat", "LP if CT negative"],
    "missing_information": ["Photophobia", "Prior headache history"],
    "urgency": "Emergent",
    "clinical_note": "Treat as SAH until proven otherwise.",
}


def _mock_groq(content_dict):
    """Return a MagicMock shaped like a Groq chat completion response."""
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps(content_dict)
    return mock_resp


# ── _validate_response: valid input ──────────────────────────────────────────

def test_validate_response_passes_for_valid_input():
    _validate_response(VALID_RESPONSE)  # should not raise


def test_validate_response_accepts_all_urgency_levels():
    for urgency in ("Emergent", "Urgent", "Semi-urgent", "Non-urgent"):
        data = {**VALID_RESPONSE, "urgency": urgency}
        _validate_response(data)  # should not raise


def test_validate_response_accepts_all_likelihood_levels():
    for likelihood in ("High", "Moderate", "Low"):
        data = copy.deepcopy(VALID_RESPONSE)
        data["possible_conditions"][0]["likelihood"] = likelihood
        _validate_response(data)  # should not raise


def test_validate_response_accepts_empty_lists():
    data = {
        **VALID_RESPONSE,
        "red_flags": [],
        "suggested_next_steps": [],
        "missing_information": [],
        "possible_conditions": [],
    }
    _validate_response(data)  # empty lists are valid


# ── _validate_response: missing top-level fields ─────────────────────────────

@pytest.mark.parametrize("missing_field", [
    "patient_summary",
    "possible_conditions",
    "red_flags",
    "suggested_next_steps",
    "missing_information",
    "urgency",
    "clinical_note",
])
def test_validate_response_raises_for_missing_top_level_field(missing_field):
    data = {k: v for k, v in VALID_RESPONSE.items() if k != missing_field}
    with pytest.raises(AIResponseValidationError, match=missing_field):
        _validate_response(data)


# ── _validate_response: possible_conditions structure ────────────────────────

def test_validate_response_raises_when_conditions_not_a_list():
    data = {**VALID_RESPONSE, "possible_conditions": "not a list"}
    with pytest.raises(AIResponseValidationError, match="list"):
        _validate_response(data)


def test_validate_response_raises_when_condition_not_a_dict():
    data = {**VALID_RESPONSE, "possible_conditions": ["string instead of dict"]}
    with pytest.raises(AIResponseValidationError):
        _validate_response(data)


@pytest.mark.parametrize("missing_cond_field", ["condition", "icd10", "likelihood", "reasoning"])
def test_validate_response_raises_for_missing_condition_field(missing_cond_field):
    data = copy.deepcopy(VALID_RESPONSE)
    del data["possible_conditions"][0][missing_cond_field]
    with pytest.raises(AIResponseValidationError, match=missing_cond_field):
        _validate_response(data)


def test_validate_response_raises_for_invalid_likelihood():
    data = copy.deepcopy(VALID_RESPONSE)
    data["possible_conditions"][0]["likelihood"] = "Possible"
    with pytest.raises(AIResponseValidationError, match="likelihood"):
        _validate_response(data)


def test_validate_response_raises_for_invalid_urgency():
    data = {**VALID_RESPONSE, "urgency": "Critical"}
    with pytest.raises(AIResponseValidationError, match="urgency"):
        _validate_response(data)


def test_validate_response_checks_all_conditions_not_just_first():
    data = copy.deepcopy(VALID_RESPONSE)
    # Second condition has invalid likelihood; first is fine
    data["possible_conditions"][1]["likelihood"] = "Maybe"
    with pytest.raises(AIResponseValidationError, match="likelihood"):
        _validate_response(data)


# ── analyze_case: success path ────────────────────────────────────────────────

def test_analyze_case_returns_validated_dict():
    with patch("app.services.ai.client.chat.completions.create",
               return_value=_mock_groq(VALID_RESPONSE)):
        result = analyze_case("65yo male with chest pain, diaphoresis, and ST elevation.")

    assert isinstance(result, dict)
    assert "patient_summary" in result
    assert "possible_conditions" in result
    assert result["urgency"] == "Emergent"


def test_analyze_case_returns_all_required_keys():
    with patch("app.services.ai.client.chat.completions.create",
               return_value=_mock_groq(VALID_RESPONSE)):
        result = analyze_case("Patient case text here for analysis.")

    required = {
        "patient_summary", "possible_conditions", "red_flags",
        "suggested_next_steps", "missing_information", "urgency", "clinical_note",
    }
    assert required.issubset(result.keys())


def test_analyze_case_truncates_long_input_to_5000_chars():
    long_text = "x" * 10_000
    captured = []

    def capture_call(**kwargs):
        user_msg = kwargs["messages"][1]["content"]
        captured.append(user_msg)
        return _mock_groq(VALID_RESPONSE)

    with patch("app.services.ai.client.chat.completions.create", side_effect=capture_call):
        analyze_case(long_text)

    # The prompt is built from case_text[:5000]; verify the embedded text is capped
    assert "x" * 5001 not in captured[0]


# ── analyze_case: error handling ─────────────────────────────────────────────

def test_analyze_case_raises_validation_error_on_bad_structure():
    bad_response = {**VALID_RESPONSE, "urgency": "NotReal"}
    with patch("app.services.ai.client.chat.completions.create",
               return_value=_mock_groq(bad_response)):
        with pytest.raises(AIResponseValidationError):
            analyze_case("case text")


def test_analyze_case_raises_value_error_on_invalid_json():
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "this is not json {{{"
    with patch("app.services.ai.client.chat.completions.create", return_value=mock_resp):
        with pytest.raises(ValueError, match="JSON"):
            analyze_case("case text")


def test_analyze_case_propagates_groq_rate_limit_error():
    import groq
    err = groq.RateLimitError.__new__(groq.RateLimitError)
    with patch("app.services.ai.client.chat.completions.create", side_effect=err):
        with pytest.raises(groq.RateLimitError):
            analyze_case("case text")


def test_analyze_case_propagates_groq_timeout_error():
    import groq
    with patch("app.services.ai.client.chat.completions.create",
               side_effect=groq.APITimeoutError("timed out")):
        with pytest.raises(groq.APITimeoutError):
            analyze_case("case text")


def test_analyze_case_propagates_groq_connection_error():
    import groq, httpx
    err = groq.APIConnectionError(
        request=httpx.Request("POST", "https://api.groq.com")
    )
    with patch("app.services.ai.client.chat.completions.create", side_effect=err):
        with pytest.raises(groq.APIConnectionError):
            analyze_case("case text")
