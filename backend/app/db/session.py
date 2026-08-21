"""Database engine and session management.

Provides a synchronous SQLAlchemy engine, a session factory, and a FastAPI
dependency (``get_db``) that yields a request-scoped session and always closes
it. ``ping_db`` is a lightweight connectivity check used by /health.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # transparently recover dropped connections
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> bool:
    """Return True if the database answers a trivial query."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
