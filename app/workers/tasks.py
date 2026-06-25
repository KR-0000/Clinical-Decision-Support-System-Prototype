import os
import logging
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

celery_app = Celery(
    "clinical_pipeline",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

# Detect whether the Redis URL uses TLS (rediss://) — Upstash requires this.
# Celery needs explicit ssl_cert_reqs when connecting to a rediss:// URL,
# otherwise it raises ValueError and refuses to start.
# CERT_NONE skips certificate verification, which is acceptable for a
# portfolio project. In production you would use CERT_REQUIRED and provide
# the CA bundle.
_redis_url = os.getenv("REDIS_URL", "")
_ssl_config = {"ssl_cert_reqs": "CERT_NONE"} if _redis_url.startswith("rediss://") else {}

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Raise SoftTimeLimitExceeded inside the task after 90 seconds.
    # Catches a hung Groq call before the hard kill fires.
    task_soft_time_limit=90,

    # Hard kill the worker thread after 120 seconds regardless.
    task_time_limit=120,

    # If the worker process is killed mid-task (OOM, docker stop),
    # reject the task back to the queue instead of losing it.
    task_reject_on_worker_lost=True,

    # SSL configuration for rediss:// URLs (Upstash in production).
    # These keys are ignored when _ssl_config is empty (local redis:// URL).
    broker_use_ssl=_ssl_config or None,
    redis_backend_use_ssl=_ssl_config or None,
)

# --- Error classification ---
#
# Not all failures are equal. Retrying a bad PDF extraction will never succeed.
# Retrying a Groq 429 rate limit will succeed after a short wait.
#
# We classify errors into two buckets:
#
# RETRYABLE: temporary external conditions — network issues, rate limits,
#            timeouts, transient API errors. Worth retrying with backoff.
#
# NON-RETRYABLE: permanent input problems — corrupted PDF, no extractable text,
#               AI returning wrong structure, missing job record. Retrying
#               wastes time and won't fix anything.
#
# The task catches these separately so we don't burn retries on permanent failures.

def _is_retryable(exc: Exception) -> bool:
    """
    Return True if the exception represents a transient condition worth retrying.
    Return False if retrying with the same input will produce the same result.
    """
    import groq

    # Groq-specific transient errors
    if isinstance(exc, (
        groq.RateLimitError,       # 429 — too many requests, back off and retry
        groq.APITimeoutError,      # request timed out
        groq.APIConnectionError,   # network connectivity issue
        groq.InternalServerError,  # 500/503 from Groq servers
    )):
        return True

    # Celery's soft time limit — the task ran too long, worth retrying
    # (maybe Groq was slow this time)
    from celery.exceptions import SoftTimeLimitExceeded
    if isinstance(exc, SoftTimeLimitExceeded):
        return True

    # Non-retryable: AI returned valid JSON but wrong structure
    from app.services.ai import AIResponseValidationError
    if isinstance(exc, AIResponseValidationError):
        return False

    # Non-retryable: PDF had no extractable text, bad file, etc.
    if isinstance(exc, ValueError):
        return False

    # 400 Bad Request errors are never transient — decommissioned model,
    # malformed request, invalid parameters. Retrying will always fail.
    if isinstance(exc, groq.BadRequestError):
        return False

    # Default: retry unknown errors once, they might be transient
    return True


@celery_app.task(bind=True, name="process_case", max_retries=3)
def process_case(self, job_id: str, input_type: str, case_text: str = None, file_ref: str = None): # type: ignore
    """
    The main worker task. Runs in a separate process from the API.

    bind=True gives access to self, needed for self.retry() and self.request.retries.
    max_retries=3 means up to 4 total attempts (1 original + 3 retries).

    Retry behavior:
    - Retryable errors (rate limits, timeouts, network): exponential backoff,
      10s -> 20s -> 40s between attempts.
    - Non-retryable errors (bad PDF, schema validation failure): mark failed
      immediately without wasting retry attempts.

    Parameters:
        job_id:     UUID of this job, used to update the DB record
        input_type: "text" or "pdf"
        case_text:  the raw text if input_type is "text"
        file_ref:   the Supabase storage path if input_type is "pdf"
    """
    # Imports are inside the function to avoid circular import issues
    # and to ensure DB sessions are created inside the worker process.
    from app.services.database import SessionLocal
    from app.models.job import Job, JobStatus
    from app.services.storage import download_file
    from app.services.pdf_extractor import extract_text
    from app.services.ai import analyze_case
    from app.services.terminology import enrich_conditions_with_verified_icd10

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            # Job record missing entirely — nothing to retry, log and exit
            logger.error(f"Job {job_id} not found in database — cannot process")
            return

        job.status = JobStatus.processing # type: ignore
        db.commit()
        logger.info(f"Job {job_id}: attempt {self.request.retries + 1} of {self.max_retries + 1}")

        # --- Step 1: Get the case text ---
        if input_type == "pdf":
            logger.info(f"Job {job_id}: downloading PDF from Supabase")
            pdf_bytes = download_file(file_ref)
            case_text = extract_text(pdf_bytes)
            logger.info(f"Job {job_id}: extracted {len(case_text)} characters from PDF")
        else:
            logger.info(f"Job {job_id}: processing text input ({len(case_text)} characters)")

        # --- Step 2: AI analysis ---
        logger.info(f"Job {job_id}: sending to Groq")
        result = analyze_case(case_text)
        logger.info(f"Job {job_id}: AI analysis complete")

        # --- Step 3: Verify ICD-10 codes against NLM ---
        # Replaces Groq's guessed codes with NLM-confirmed codes where possible.
        # Adds icd10_verified=True/False to each condition so the result is
        # honest about which codes were confirmed. Never raises — if NLM is
        # unreachable, conditions keep Groq's original codes with verified=False.
        logger.info(f"Job {job_id}: verifying ICD-10 codes against NLM")
        result["possible_conditions"] = enrich_conditions_with_verified_icd10(
            result["possible_conditions"]
        )
        verified_count = sum(
            1 for c in result["possible_conditions"] if c.get("icd10_verified")
        )
        logger.info(
            f"Job {job_id}: {verified_count}/{len(result['possible_conditions'])} "
            f"ICD-10 codes verified by NLM"
        )

        # --- Step 4: Save result ---
        job.status = JobStatus.done # type: ignore
        job.result = result # type: ignore
        db.commit()
        logger.info(f"Job {job_id}: complete")

    except Exception as exc:
        attempt = self.request.retries + 1
        logger.error(f"Job {job_id}: error on attempt {attempt} — {type(exc).__name__}: {exc}")

        retryable = _is_retryable(exc)
        retries_left = self.max_retries - self.request.retries

        if retryable and retries_left > 0:
            # Reset to pending so the status endpoint doesn't show
            # "processing" during the wait between retries
            try:
                job = db.query(Job).filter(Job.job_id == job_id).first()
                if job:
                    job.status = JobStatus.pending # type: ignore
                    db.commit()
            except Exception:
                pass  # DB update failure during retry handling shouldn't mask original error

            # Exponential backoff: 10s, 20s, 40s
            countdown = 10 * (2 ** self.request.retries)
            logger.info(
                f"Job {job_id}: retryable error ({type(exc).__name__}), "
                f"retrying in {countdown}s ({retries_left} attempt(s) left)"
            )
            raise self.retry(exc=exc, countdown=countdown)

        else:
            # Either non-retryable, or we have exhausted all retries
            if not retryable:
                reason = f"Non-retryable error: {type(exc).__name__}: {exc}"
                logger.error(f"Job {job_id}: failing immediately — {reason}")
            else:
                reason = f"All {self.max_retries + 1} attempts failed. Last error: {exc}"
                logger.error(f"Job {job_id}: {reason}")

            try:
                job = db.query(Job).filter(Job.job_id == job_id).first()
                if job:
                    job.status = JobStatus.failed # type: ignore
                    job.error_message = str(exc) # type: ignore
                    db.commit()
            except Exception as db_exc:
                logger.error(f"Job {job_id}: failed to write failed status to DB — {db_exc}")

    finally:
        db.close()