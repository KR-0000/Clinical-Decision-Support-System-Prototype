import io
import pdfplumber


def extract_text(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF given its raw bytes.

    pdfplumber works page by page. We collect text from each page
    and join them with double newlines to preserve document structure.

    Raises ValueError if no text is found. This happens with:
    - Scanned PDFs that are images with no embedded text layer
    - Corrupted or password-protected PDFs

    The caller (the Celery worker) catches this and marks the job as failed
    with a clear error message rather than crashing.
    """
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pages = []
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())

    if not pages:
        raise ValueError(
            "No readable text found in this PDF. "
            "It may be a scanned document. "
            "Please use a PDF with embedded text, or type the case details directly."
        )

    return "\n\n".join(pages)