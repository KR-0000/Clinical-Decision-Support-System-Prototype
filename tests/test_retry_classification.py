"""
Tests for _is_retryable() in app/workers/tasks.py.

Verifies which exception types cause the worker to retry vs fail immediately.
No DB, no Celery, no network — pure function logic.
"""

import pytest
import httpx
import groq
from celery.exceptions import SoftTimeLimitExceeded

from app.services.ai import AIResponseValidationError
from app.workers.tasks import _is_retryable

# Shared httpx request/responses used to construct groq errors
_REQ = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
_R429 = httpx.Response(429, request=_REQ)
_R400 = httpx.Response(400, request=_REQ)
_R500 = httpx.Response(500, request=_REQ)


# ── Retryable errors ──────────────────────────────────────────────────────────

def test_rate_limit_error_is_retryable():
    exc = groq.RateLimitError("rate limit", response=_R429, body={})
    assert _is_retryable(exc) is True


def test_timeout_error_is_retryable():
    exc = groq.APITimeoutError("request timed out")
    assert _is_retryable(exc) is True


def test_connection_error_is_retryable():
    exc = groq.APIConnectionError(request=_REQ)
    assert _is_retryable(exc) is True


def test_internal_server_error_is_retryable():
    exc = groq.InternalServerError("500 from Groq", response=_R500, body={})
    assert _is_retryable(exc) is True


def test_soft_time_limit_is_retryable():
    exc = SoftTimeLimitExceeded()
    assert _is_retryable(exc) is True


# ── Non-retryable errors ──────────────────────────────────────────────────────

def test_bad_request_error_is_not_retryable():
    exc = groq.BadRequestError("decommissioned model", response=_R400, body={})
    assert _is_retryable(exc) is False


def test_ai_response_validation_error_is_not_retryable():
    exc = AIResponseValidationError("AI returned wrong structure")
    assert _is_retryable(exc) is False


def test_value_error_is_not_retryable():
    exc = ValueError("No readable text found in PDF")
    assert _is_retryable(exc) is False


def test_value_error_subclass_is_not_retryable():
    class ScannedPdfError(ValueError):
        pass
    exc = ScannedPdfError("Scanned PDF has no text layer")
    assert _is_retryable(exc) is False


# ── Default / unknown errors ──────────────────────────────────────────────────

def test_unknown_exception_defaults_to_retryable():
    exc = RuntimeError("unexpected database error")
    assert _is_retryable(exc) is True


def test_generic_exception_defaults_to_retryable():
    exc = Exception("something went wrong")
    assert _is_retryable(exc) is True


def test_os_error_defaults_to_retryable():
    exc = OSError("network interface unavailable")
    assert _is_retryable(exc) is True


# ── Boundary: AIResponseValidationError IS a ValueError subclass ──────────────

def test_ai_validation_error_classified_before_value_error_check():
    # AIResponseValidationError inherits from ValueError. The function must check
    # AIResponseValidationError first — otherwise the ValueError branch would fire
    # but the distinction matters for error messages. Both return False, which is
    # what we verify here. Ordering in the function is an implementation detail.
    exc = AIResponseValidationError("missing field: urgency")
    assert _is_retryable(exc) is False


# ── Multiple retries scenario: same error stays retryable ────────────────────

def test_rate_limit_stays_retryable_across_multiple_checks():
    exc = groq.RateLimitError("rate limit", response=_R429, body={})
    assert _is_retryable(exc) is True
    assert _is_retryable(exc) is True
    assert _is_retryable(exc) is True
