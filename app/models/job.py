import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel

from app.services.database import Base


class JobStatus(str, enum.Enum):
    """
    The valid states a job can be in.

    Using an enum instead of plain strings prevents bugs like
    status="procesing" (typo) going undetected.

    Inheriting from str means this serializes to a plain string
    in JSON responses automatically.
    """
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class Job(Base):
    """
    SQLAlchemy model — maps directly to the 'jobs' table in Postgres.
    Each Column() attribute becomes a column in the table.

    Alembic reads this class to generate migration scripts when you change it.
    """
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True, index=True)

    # What kind of input was submitted: "text" or "pdf"
    input_type = Column(String, nullable=False)

    status = Column(SAEnum(JobStatus), default=JobStatus.pending, nullable=False)

    # Path in Supabase Storage — only set for PDF jobs, null for text jobs
    file_ref = Column(String, nullable=True)

    # The structured output from the AI, stored as JSON
    result = Column(JSON, nullable=True)

    # What went wrong, if anything — helps debug failed jobs
    error_message = Column(Text, nullable=True)

    # server_default means Postgres sets this at insert time, not Python.
    # More reliable in distributed systems where clocks may differ.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# --- Pydantic response schemas ---
# These are separate from the SQLAlchemy model.
# The SQLAlchemy model defines what is stored in the database.
# Pydantic schemas define what shape the API returns to callers.
# Keeping them separate means you can return different fields than you store.

class JobCreateResponse(BaseModel):
    """Returned immediately when a job is created via POST /jobs/upload."""
    job_id: str
    status: JobStatus
    input_type: str

    class Config:
        # Allows Pydantic to read attributes from SQLAlchemy objects
        # instead of requiring plain dicts.
        from_attributes = True


class JobStatusResponse(BaseModel):
    """Returned from GET /jobs/status/{job_id}."""
    job_id: str
    status: JobStatus
    input_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class JobResultResponse(BaseModel):
    """Returned from GET /jobs/result/{job_id}."""
    job_id: str
    status: JobStatus
    result: Optional[dict] = None
    error_message: Optional[str] = None