import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# SessionLocal is a factory that creates new database sessions.
# autocommit=False means changes are not saved until you explicitly call db.commit().
# autoflush=False means SQLAlchemy won't auto-send pending changes before queries.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this class.
    It keeps track of every model so Alembic can detect schema changes.
    """
    pass


def get_db():
    """
    FastAPI dependency function.

    Use it in endpoint signatures like: db: Session = Depends(get_db)
    FastAPI will call this function, get the session, pass it to your endpoint,
    and then close the session when the request finishes — even if an exception occurs.

    The 'yield' makes this a generator. Code before yield runs before the endpoint.
    Code after yield (the finally block) runs after the endpoint returns.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()