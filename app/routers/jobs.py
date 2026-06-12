import uuid
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus, JobCreateResponse, JobStatusResponse, JobResultResponse
from app.services.database import get_db
from app.services.storage import upload_file
from app.workers.tasks import process_case

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=JobCreateResponse)
async def upload_case(
    case_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Submit a clinical case for analysis.

    Accepts either:
    - case_text: a typed case description (symptoms, vitals, history)
    - file: a PDF clinical note upload

    One of the two must be provided. If both are provided, the PDF takes priority.

    Returns a job_id immediately. The actual processing happens asynchronously
    in the Celery worker. Use /jobs/status/{job_id} to check progress.
    """

    # Validate that at least one input was provided
    if not case_text and not file:
        raise HTTPException(
            status_code=400,
            detail="Provide either case_text or a PDF file upload."
        )

    job_id = str(uuid.uuid4())

    # --- Handle PDF upload ---
    if file:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted. For other formats, copy the text into case_text."
            )

        logger.info(f"Job {job_id}: PDF upload received — {file.filename}")
        file_bytes = await file.read()

        try:
            file_ref = upload_file(file_bytes, file.filename, job_id)
            logger.info(f"Job {job_id}: file stored at {file_ref}")
        except Exception as e:
            logger.error(f"Job {job_id}: storage upload failed — {e}")
            raise HTTPException(status_code=500, detail="Failed to store uploaded file.")

        # Create job record in DB
        job = Job(job_id=job_id, input_type="pdf", status=JobStatus.pending, file_ref=file_ref)
        db.add(job)
        db.commit()

        # Queue the task — .delay() posts to Redis and returns immediately
        # The worker picks this up asynchronously
        process_case.delay(job_id=job_id, input_type="pdf", file_ref=file_ref)

    # --- Handle text input ---
    else:
        if len(case_text.strip()) < 20:
            raise HTTPException(
                status_code=400,
                detail="Case description is too short. Please provide more clinical detail."
            )

        logger.info(f"Job {job_id}: text case received ({len(case_text)} characters)")

        job = Job(job_id=job_id, input_type="text", status=JobStatus.pending)
        db.add(job)
        db.commit()

        process_case.delay(job_id=job_id, input_type="text", case_text=case_text)

    logger.info(f"Job {job_id}: queued successfully")
    db.refresh(job)
    return job


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str, db: Session = Depends(get_db)):
    """
    Check the current status of a job.

    Status values:
    - pending: job is in the queue, worker has not started yet
    - processing: worker is actively analyzing the case
    - done: analysis complete, result is available
    - failed: analysis failed after all retries, error_message explains why
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job


@router.get("/result/{job_id}", response_model=JobResultResponse)
def get_result(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the analysis result for a completed job.

    If the job is not yet done, returns the current status with no result.
    If the job failed, returns the error message.
    If the job is done, returns the full structured clinical differential.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    return JobResultResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result if job.status == JobStatus.done else None,
        error_message=job.error_message if job.status == JobStatus.failed else None
    )