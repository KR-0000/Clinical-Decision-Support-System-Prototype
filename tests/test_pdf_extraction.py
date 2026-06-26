"""
Tests for app/services/pdf_extractor.py.

pdfplumber is mocked throughout — tests verify extraction logic and error handling,
not pdfplumber internals.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.pdf_extractor import extract_text


def _make_mock_pdf(*page_texts):
    """Build a mock pdfplumber PDF context manager with given per-page text strings."""
    pages = []
    for text in page_texts:
        page = MagicMock()
        page.extract_text.return_value = text
        pages.append(page)

    mock_pdf = MagicMock()
    mock_pdf.pages = pages
    mock_pdf.__enter__ = lambda s: s
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


# ── Success paths ─────────────────────────────────────────────────────────────

def test_extract_text_returns_string_for_single_page():
    with patch("app.services.pdf_extractor.pdfplumber.open",
               return_value=_make_mock_pdf("Patient: Jane Doe\nChief complaint: headache")):
        result = extract_text(b"fake pdf bytes")
    assert "Jane Doe" in result
    assert "headache" in result


def test_extract_text_joins_multipage_with_double_newline():
    with patch("app.services.pdf_extractor.pdfplumber.open",
               return_value=_make_mock_pdf("Page one content", "Page two content")):
        result = extract_text(b"fake multipage pdf")
    assert "Page one content" in result
    assert "Page two content" in result
    assert "\n\n" in result


def test_extract_text_strips_whitespace_from_pages():
    with patch("app.services.pdf_extractor.pdfplumber.open",
               return_value=_make_mock_pdf("  padded text  ")):
        result = extract_text(b"fake pdf")
    assert result == "padded text"


def test_extract_text_skips_blank_pages():
    with patch("app.services.pdf_extractor.pdfplumber.open",
               return_value=_make_mock_pdf("Real page", "", None, "   ", "Another page")):
        result = extract_text(b"pdf with blank pages")
    # Blank/None/whitespace-only pages should not appear in output
    assert result == "Real page\n\nAnother page"


def test_extract_text_works_with_many_pages():
    pages = [f"Clinical note section {i}" for i in range(10)]
    with patch("app.services.pdf_extractor.pdfplumber.open",
               return_value=_make_mock_pdf(*pages)):
        result = extract_text(b"long pdf")
    assert "section 0" in result
    assert "section 9" in result


# ── Error paths ───────────────────────────────────────────────────────────────

def test_extract_text_raises_value_error_for_empty_pdf():
    with patch("app.services.pdf_extractor.pdfplumber.open",
               return_value=_make_mock_pdf()):
        with pytest.raises(ValueError, match="No readable text"):
            extract_text(b"empty pdf")


def test_extract_text_raises_value_error_when_all_pages_have_no_text():
    with patch("app.services.pdf_extractor.pdfplumber.open",
               return_value=_make_mock_pdf(None, None, None)):
        with pytest.raises(ValueError, match="No readable text"):
            extract_text(b"scanned pdf with no text layer")


def test_extract_text_raises_value_error_when_pages_are_whitespace_only():
    with patch("app.services.pdf_extractor.pdfplumber.open",
               return_value=_make_mock_pdf("   ", "\n\n\t", "  ")):
        with pytest.raises(ValueError, match="No readable text"):
            extract_text(b"whitespace only pdf")


def test_extract_text_propagates_pdfplumber_exceptions():
    with patch("app.services.pdf_extractor.pdfplumber.open",
               side_effect=Exception("corrupted PDF structure")):
        with pytest.raises(Exception, match="corrupted"):
            extract_text(b"bad bytes")
