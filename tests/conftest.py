"""Pytest fixtures providing in-memory database and synthetic mock test artifacts.

Note: In accordance with security guidelines, all fixtures use purely synthetic
mock data without sensitive or proprietary organizational content.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from iso_assistant.db.connection import Base
from iso_assistant.db.models import Project


@pytest.fixture(scope="function")
def in_memory_db() -> Generator[Session, None, None]:
    """Provides an isolated, in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def sample_project(in_memory_db: Session) -> Project:
    """Creates a sample test project in the test database."""
    project = Project(
        name="Test ISMS Project",
        organization_name="Acme Corp Synthetic",
        scope_description="Testing scope covering cloud infrastructure.",
    )
    in_memory_db.add(project)
    in_memory_db.commit()
    in_memory_db.refresh(project)
    return project

