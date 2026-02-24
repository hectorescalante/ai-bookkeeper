"""Pytest fixtures for API integration tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.adapters.persistence.database import Base, get_db

# Import models FIRST to register with Base.metadata
from backend.adapters.persistence.models import (  # noqa: F401
    AgentModel,
    BookingModel,
    ClientInvoiceModel,
    ClientModel,
    CompanyModel,
    DocumentModel,
    OutlookOAuthStateModel,
    ProviderInvoiceModel,
    ProviderModel,
    SettingsModel,
)
from backend.main import app


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create a new database session for test fixtures."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_engine):
    """Create a test client with database dependency override."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
