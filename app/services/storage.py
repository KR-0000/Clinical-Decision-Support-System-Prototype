import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Create the Supabase client once at module load time.
# It gets reused for every upload/download call.
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

BUCKET = "clinical-notes"


def upload_file(file_bytes: bytes, filename: str, job_id: str) -> str:
    """
    Upload a PDF to Supabase Storage.

    Files are stored under a path that includes the job_id:
        "abc-123-uuid/clinical_note.pdf"

    This keeps each job's files in their own folder and makes
    it easy to find or delete files for a specific job.

    Returns the storage path, which is saved as file_ref in the DB.
    """
    path = f"{job_id}/{filename}"
    supabase.storage.from_(BUCKET).upload(
        path,
        file_bytes,
        {"content-type": "application/pdf"}
    )
    return path


def download_file(file_ref: str) -> bytes:
    """
    Download a file from Supabase by its storage path.

    Called by the Celery worker when processing a PDF job.
    The file_ref comes from the job record in Postgres.
    """
    return supabase.storage.from_(BUCKET).download(file_ref)