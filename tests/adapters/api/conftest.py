"""Pytest fixtures for API integration tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.adapters.persistence.database import Base, get_db
from backend.main import app


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    # Import all models to register them with Base.metadata
    from backend.adapters.persistence.models import (  # noqa: F401
        AgentModel,
        BookingModel,
        ClientInvoiceModel,
        ClientModel,
        CompanyModel,
        DocumentModel,
        ProviderInvoiceModel,
        ProviderModel,
        SettingsModel,
    )

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
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
def client(db_session):
    """Create a test client with database dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
