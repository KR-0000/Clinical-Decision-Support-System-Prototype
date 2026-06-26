import os

# Must be set before any app module is imported. conftest.py is loaded first
# by pytest, so placing these at module level ensures they're visible when
# database.py, storage.py, and ai.py run their module-level setup.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "eyJtest.supabase.service_role_key")
os.environ.setdefault("GROQ_API_KEY", "gsk_test_key")

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.services.database import Base, get_db
from app.limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset in-memory rate limit counters before every test."""
    limiter.reset()
    yield


@pytest.fixture(scope="function")
def test_engine():
    """
    Per-test in-memory SQLite engine with StaticPool.
    StaticPool forces all SQLAlchemy operations to share the same underlying
    connection, which is required for sqlite:// (no path) because each new
    connection would otherwise open a fresh empty database.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Direct DB session for use in non-endpoint tests (e.g. worker task tests)."""
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_engine):
    """
    FastAPI TestClient with:
    - SQLite in-memory DB (overrides get_db dependency)
    - process_case.delay mocked (no Redis connection)
    - upload_file mocked (no Supabase connection)

    Attributes attached to the returned client:
      client.mock_task   — MagicMock for app.routers.jobs.process_case
      client.mock_upload — MagicMock for app.routers.jobs.upload_file
    """
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    def _override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db

    with patch("app.routers.jobs.process_case") as mock_task, \
         patch("app.routers.jobs.upload_file") as mock_upload:
        mock_task.delay.return_value = MagicMock()
        mock_upload.return_value = "mock-job-id/file.pdf"
        with TestClient(app, raise_server_exceptions=True) as c:
            c.mock_task = mock_task
            c.mock_upload = mock_upload
            yield c

    app.dependency_overrides.clear()
