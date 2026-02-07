"""Pytest fixtures for repository integration tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.adapters.persistence.database import Base


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def clean_db_session(db_engine):
    """Create a clean session that auto-commits for testing."""
    SessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=True)
    session = SessionLocal()
    yield session
    session.close()
