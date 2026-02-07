"""Integration tests for documents API endpoints."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.domain.entities.document import Document
from backend.domain.enums import DocumentType, ProcessingStatus
from backend.domain.value_objects import EmailReference, FileHash


@pytest.fixture
def sample_documents(db_session):
    """Create sample documents for testing."""
    from backend.adapters.persistence.repositories.document_repository import (
        SqlAlchemyDocumentRepository,
    )

    repo = SqlAlchemyDocumentRepository(db_session)

    # Create pending document
    doc1 = Document.create(
        filename="invoice1.pdf",
        file_hash=FileHash.sha256("abc123"),
        email_reference=EmailReference(
            message_id="msg-123",
            subject="Invoice",
            sender="sender@example.com",
            received_at=datetime.now(),
        ),
    )
    repo.save(doc1)

    # Create processed document
    doc2 = Document.create(filename="invoice2.pdf", file_hash=FileHash.sha256("def456"))
    doc2.mark_processed(DocumentType.CLIENT_INVOICE)
    repo.save(doc2)

    db_session.commit()
    return [doc1, doc2]


def test_list_all_documents(client: TestClient, sample_documents) -> None:
    """Test GET /api/documents without filters."""
    response = client.get("/api/documents")

    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["documents"]) == 2


def test_list_documents_by_status(client: TestClient, sample_documents) -> None:
    """Test GET /api/documents with status filter."""
    response = client.get("/api/documents?status=PENDING")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["documents"][0]["status"] == "PENDING"
    assert data["documents"][0]["filename"] == "invoice1.pdf"


def test_list_documents_with_limit(client: TestClient, sample_documents) -> None:
    """Test GET /api/documents with limit."""
    response = client.get("/api/documents?limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 1


def test_list_documents_invalid_status(client: TestClient) -> None:
    """Test GET /api/documents with invalid status."""
    response = client.get("/api/documents?status=INVALID")

    assert response.status_code == 400  # ValueError -> 400
    assert "validation_error" in response.json()["error_type"]


def test_document_list_includes_email_info(client: TestClient, sample_documents) -> None:
    """Test that document list includes email information."""
    response = client.get("/api/documents?status=PENDING")

    assert response.status_code == 200
    data = response.json()
    doc = data["documents"][0]
    assert doc["email_sender"] == "sender@example.com"
    assert doc["email_subject"] == "Invoice"


def test_list_processed_documents(client: TestClient, sample_documents) -> None:
    """Test listing processed documents."""
    response = client.get("/api/documents?status=PROCESSED")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["documents"][0]["status"] == "PROCESSED"
    assert data["documents"][0]["document_type"] == "CLIENT_INVOICE"
