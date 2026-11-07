"""Database engine setup, session management, and lifecycle handling for SQLite."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from iso_assistant.config import settings
from iso_assistant.utils.logger import get_logger

logger = get_logger(__name__)


# Enforce foreign key constraints and WAL journal mode on SQLite connections
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enables SQLite foreign key support and Write-Ahead Logging for concurrency."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.close()


# Ensure data directory exists
db_path = settings.database_url.replace("sqlite:///", "")
Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for Streamlit thread safety
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class DatabaseSchemaError(RuntimeError):
    """Raised when existing database schema is incompatible with current models."""


def _check_schema_compatibility(eng: Engine) -> None:
    """Verifies that an existing database matches the current model definitions.

    If an outdated schema is detected (e.g., missing columns), logs an informative error
    and raises DatabaseSchemaError instructing the developer to recreate the development/testing
    database manually. Does NOT drop or alter existing tables or delete user data automatically.
    """
    from iso_assistant.db.models import Document

    inspector = inspect(eng)
    if not inspector.has_table(Document.__tablename__):
        return

    existing_cols = {c["name"] for c in inspector.get_columns(Document.__tablename__)}
    model_cols = {c.name for c in Document.__table__.columns}
    missing_cols = model_cols - existing_cols

    if missing_cols:
        error_msg = (
            f"Database schema compatibility error: Table '{Document.__tablename__}' "
            f"is missing expected column(s): {sorted(missing_cols)}. "
            f"Automatic migrations are disabled for this stage. "
            f"Please recreate your local SQLite database manually "
            f"(e.g. backup and delete the SQLite database file: '{settings.database_url}')."
        )
        logger.error(error_msg)
        raise DatabaseSchemaError(error_msg)


def init_db() -> None:
    """Initializes SQLite schema by creating all registered declarative tables.

    Safe for repeated invocations on databases with matching/current schema.
    Raises DatabaseSchemaError if an existing database has an outdated schema.
    """
    # Import all models to ensure registration on metadata
    from iso_assistant.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _check_schema_compatibility(engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provides a transactional database session scope."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

