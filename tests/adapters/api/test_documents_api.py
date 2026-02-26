"""Integration tests for documents API endpoints."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.adapters.persistence.repositories.document_repository import (
    SqlAlchemyDocumentRepository,
)
from backend.adapters.persistence.repositories.invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from backend.adapters.persistence.repositories.party_repositories import (
    SqlAlchemyProviderRepository,
)
from backend.application.dtos.document_dtos import FetchEmailsResponse as FetchEmailsResponseDto
from backend.application.dtos.invoice_dtos import ProcessInvoiceResponse
from backend.config.dependencies import get_fetch_emails_use_case, get_process_invoice_use_case
from backend.domain.entities.document import Document
from backend.domain.entities.invoice import ProviderInvoice
from backend.domain.entities.party import Provider
from backend.domain.enums import DocumentType, ProviderType
from backend.domain.value_objects import EmailReference, FileHash, Money
from backend.main import app


@pytest.fixture
def sample_documents(db_session):
    """Create sample documents for testing."""

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
    _ = sample_documents
    response = client.get("/api/documents")

    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["documents"]) == 2


def test_list_documents_by_status(client: TestClient, sample_documents) -> None:
    """Test GET /api/documents with status filter."""
    _ = sample_documents
    response = client.get("/api/documents?status=PENDING")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["documents"][0]["status"] == "PENDING"
    assert data["documents"][0]["filename"] == "invoice1.pdf"


def test_list_documents_with_limit(client: TestClient, sample_documents) -> None:
    """Test GET /api/documents with limit."""
    _ = sample_documents
    response = client.get("/api/documents?limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 1


def test_list_documents_invalid_status(client: TestClient) -> None:
    """Test GET /api/documents with invalid status."""
    response = client.get("/api/documents?status=INVALID")
    assert response.status_code == 422


def test_document_list_includes_email_info(client: TestClient, sample_documents) -> None:
    """Test that document list includes email information."""
    _ = sample_documents
    response = client.get("/api/documents?status=PENDING")

    assert response.status_code == 200
    data = response.json()
    doc = data["documents"][0]
    assert doc["email_sender"] == "sender@example.com"
    assert doc["email_subject"] == "Invoice"


def test_list_processed_documents(client: TestClient, sample_documents) -> None:
    """Test listing processed documents."""
    _ = sample_documents
    response = client.get("/api/documents?status=PROCESSED")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["documents"][0]["status"] == "PROCESSED"
    assert data["documents"][0]["document_type"] == "CLIENT_INVOICE"


@pytest.fixture
def processed_provider_document(db_session, tmp_path):
    """Create a processed provider document with invoice metadata and source file."""
    document_repo = SqlAlchemyDocumentRepository(db_session)
    invoice_repo = SqlAlchemyInvoiceRepository(db_session)
    provider_repo = SqlAlchemyProviderRepository(db_session)

    provider = Provider.create(
        nif="B99112233",
        provider_type=ProviderType.CARRIER,
        name="Maersk Logistics",
    )
    provider_repo.save(provider)

    invoice = ProviderInvoice.create(
        invoice_number="SUP-001",
        provider_id=provider.id,
        provider_type=ProviderType.CARRIER,
        invoice_date=date(2024, 1, 15),
        bl_references=["BL-ABC-001", "BL-XYZ-009"],
        total_amount=Money(Decimal("300.00")),
        tax_amount=Money(Decimal("0.00")),
    )
    invoice_repo.save_provider_invoice(invoice)

    file_path = tmp_path / "provider-invoice.pdf"
    file_path.write_bytes(b"%PDF-1.4 provider invoice test")

    document = Document.create(
        filename="provider-invoice.pdf",
        file_hash=FileHash.sha256("provider-001"),
        storage_path=str(file_path),
    )
    document.mark_processed(DocumentType.PROVIDER_INVOICE, invoice.id)
    document_repo.save(document)
    return document


def test_list_documents_filtered_by_provider_party_and_booking(
    client: TestClient, processed_provider_document
) -> None:
    """Test processed filters by party and booking include enriched metadata."""
    document = processed_provider_document
    response = client.get(
        "/api/documents?status=PROCESSED&document_type=PROVIDER_INVOICE&party=maersk&booking=BL-ABC"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    item = payload["documents"][0]
    assert item["id"] == str(document.id)
    assert item["invoice_number"] == "SUP-001"
    assert item["party_name"] == "Maersk Logistics"
    assert item["booking_references"] == ["BL-ABC-001", "BL-XYZ-009"]
    assert item["total_amount"] == "300.00"
    assert item["file_url"] == f"/api/documents/{document.id}/file"


def test_list_documents_invalid_date_range_returns_400(client: TestClient) -> None:
    """Test list documents rejects invalid date ranges."""
    response = client.get("/api/documents?date_from=2024-02-01&date_to=2024-01-01")
    assert response.status_code == 400
    assert "date_from cannot be greater than date_to" in response.json()["detail"]


def test_get_document_file_success(
    client: TestClient, processed_provider_document
) -> None:
    """Test document file endpoint returns PDF content."""
    document = processed_provider_document
    response = client.get(f"/api/documents/{document.id}/file")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-1.4")


def test_get_document_file_not_available_returns_404(
    client: TestClient, sample_documents
) -> None:
    """Test document file endpoint returns 404 when storage path is absent."""
    pending_document = sample_documents[0]
    response = client.get(f"/api/documents/{pending_document.id}/file")
    assert response.status_code == 404
    assert "not available" in response.json()["detail"].lower()


class _StubFetchEmailsUseCase:
    def __init__(
        self,
        response: FetchEmailsResponseDto | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error

    def execute(self, _request):  # noqa: ANN001
        self.last_request = _request
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


class _StubProcessInvoiceUseCase:
    def __init__(
        self,
        response: ProcessInvoiceResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error
        self.last_request = None

    def execute(self, _request):  # noqa: ANN001
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


def test_fetch_emails_endpoint_success(client: TestClient) -> None:
    app.dependency_overrides[get_fetch_emails_use_case] = lambda: _StubFetchEmailsUseCase(
        response=FetchEmailsResponseDto(
            scanned_messages=3,
            pdf_attachments_found=5,
            imported_documents=4,
            duplicate_documents=1,
        )
    )
    try:
        response = client.post("/api/documents/fetch", json={"max_messages": 20})
    finally:
        app.dependency_overrides.pop(get_fetch_emails_use_case, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["scanned_messages"] == 3
    assert payload["pdf_attachments_found"] == 5
    assert payload["imported_documents"] == 4
    assert payload["duplicate_documents"] == 1


def test_fetch_emails_endpoint_outlook_not_connected(client: TestClient) -> None:
    app.dependency_overrides[get_fetch_emails_use_case] = lambda: _StubFetchEmailsUseCase(
        error=ValueError("Outlook is not connected. Configure Outlook in Settings first.")
    )
    try:
        response = client.post("/api/documents/fetch", json={"max_messages": 20})
    finally:
        app.dependency_overrides.pop(get_fetch_emails_use_case, None)

    assert response.status_code == 400
    assert "Outlook is not connected" in response.json()["detail"]


def test_retry_document_endpoint_success(client: TestClient) -> None:
    document_id = uuid4()
    app.dependency_overrides[get_process_invoice_use_case] = (
        lambda: _StubProcessInvoiceUseCase(
            response=ProcessInvoiceResponse(
                document_id=document_id,
                document_type="CLIENT_INVOICE",
                document_type_confidence="HIGH",
                ai_model="gemini-3-pro",
                raw_json="{\"document_type\":\"CLIENT_INVOICE\"}",
                invoice_number="INV-123",
                invoice_date="2024-01-01",
                issuer_name="Issuer",
                issuer_nif="B11111111",
                recipient_name="Recipient",
                recipient_nif="B22222222",
                provider_type=None,
                currency_valid=True,
                currency_detected="EUR",
                bl_references=[{"bl_number": "BL-001"}],
                charges=[],
                totals={"total": "100.00"},
                extraction_notes=None,
                overall_confidence="HIGH",
                warnings=[],
                errors=[],
            )
        )
    )
    try:
        response = client.post(f"/api/documents/{document_id}/retry")
    finally:
        app.dependency_overrides.pop(get_process_invoice_use_case, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == str(document_id)
    assert payload["document_type"] == "CLIENT_INVOICE"
    assert payload["invoice_number"] == "INV-123"


def test_retry_document_endpoint_rate_limit_maps_to_429(client: TestClient) -> None:
    document_id = uuid4()
    app.dependency_overrides[get_process_invoice_use_case] = (
        lambda: _StubProcessInvoiceUseCase(
            error=ValueError("AI rate limit reached. Try again in 2 minutes.")
        )
    )
    try:
        response = client.post(f"/api/documents/{document_id}/retry")
    finally:
        app.dependency_overrides.pop(get_process_invoice_use_case, None)

    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


def test_reprocess_document_endpoint_success(client: TestClient) -> None:
    document_id = uuid4()
    stub = _StubProcessInvoiceUseCase(
        response=ProcessInvoiceResponse(
            document_id=document_id,
            document_type="CLIENT_INVOICE",
            document_type_confidence="HIGH",
            ai_model="gemini-3-pro",
            raw_json="{\"document_type\":\"CLIENT_INVOICE\"}",
            invoice_number="INV-555",
            invoice_date="2024-01-02",
            issuer_name="Issuer",
            issuer_nif="B11111111",
            recipient_name="Recipient",
            recipient_nif="B22222222",
            provider_type=None,
            currency_valid=True,
            currency_detected="EUR",
            bl_references=[{"bl_number": "BL-002"}],
            charges=[],
            totals={"total": "120.00"},
            extraction_notes=None,
            overall_confidence="HIGH",
            warnings=[],
            errors=[],
        )
    )
    app.dependency_overrides[get_process_invoice_use_case] = lambda: stub
    try:
        response = client.post(f"/api/documents/{document_id}/reprocess")
    finally:
        app.dependency_overrides.pop(get_process_invoice_use_case, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == str(document_id)
    assert payload["invoice_number"] == "INV-555"
    assert payload["document_type"] == "CLIENT_INVOICE"


def test_reprocess_document_endpoint_timeout_maps_to_504(client: TestClient) -> None:
    document_id = uuid4()
    app.dependency_overrides[get_process_invoice_use_case] = (
        lambda: _StubProcessInvoiceUseCase(
            error=ValueError("AI processing timed out. Please retry.")
        )
    )
    try:
        response = client.post(f"/api/documents/{document_id}/reprocess")
    finally:
        app.dependency_overrides.pop(get_process_invoice_use_case, None)

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()
