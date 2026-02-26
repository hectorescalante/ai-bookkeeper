"""Integration tests for invoice processing API endpoints."""
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.adapters.persistence.repositories.document_repository import (
    SqlAlchemyDocumentRepository,
)
from backend.adapters.persistence.repositories.invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from backend.adapters.persistence.repositories.party_repositories import (
    SqlAlchemyClientRepository,
    SqlAlchemyProviderRepository,
)
from backend.domain.entities.document import Document
from backend.domain.entities.invoice import ClientInvoice, ProviderInvoice
from backend.domain.entities.party import Client, Provider
from backend.domain.enums import ProviderType
from backend.domain.value_objects import FileHash, Money


@pytest.fixture
def pending_document(db_session):
    """Create a pending document for confirm/save endpoint tests."""
    repo = SqlAlchemyDocumentRepository(db_session)
    document = Document.create(
        filename="invoice.pdf",
        file_hash=FileHash.sha256("api-doc-hash"),
        storage_path="/tmp/invoice.pdf",
    )
    repo.save(document)
    return document


def test_confirm_client_invoice_persists_and_marks_document_processed(
    client: TestClient, pending_document
) -> None:
    response = client.post(
        "/api/invoices/confirm",
        json={
            "document_id": str(pending_document.id),
            "document_type": "CLIENT_INVOICE",
            "ai_model": "gemini-3-pro",
            "raw_json": "{\"document_type\":\"CLIENT_INVOICE\"}",
            "overall_confidence": "HIGH",
            "invoice_number": "INV-100",
            "invoice_date": "2024-01-15",
            "issuer_name": "Our Company",
            "issuer_nif": "B00000000",
            "recipient_name": "Client A",
            "recipient_nif": "C11111111",
            "bl_references": ["BL-001"],
            "charges": [
                {
                    "bl_reference": "BL-001",
                    "description": "Ocean Freight",
                    "category": "FREIGHT",
                    "amount": "1000.00",
                }
            ],
            "totals": {"tax_amount": "210.00", "total": "1210.00"},
            "shipping_details": {
                "pol": {"code": "CNSHA", "name": "Shanghai"},
                "pod": {"code": "ESVLC", "name": "Valencia"},
                "vessel": "MSC Test",
                "containers": ["CONT-001"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == str(pending_document.id)
    assert payload["invoice_id"] is not None
    assert payload["document_type"] == "CLIENT_INVOICE"
    assert payload["status"] == "PROCESSED"
    assert payload["booking_ids"] == ["BL-001"]

    # Verify document appears as processed
    documents_response = client.get("/api/documents?status=PROCESSED")
    assert documents_response.status_code == 200
    documents_payload = documents_response.json()
    assert documents_payload["total"] == 1
    assert documents_payload["documents"][0]["id"] == str(pending_document.id)
    assert documents_payload["documents"][0]["document_type"] == "CLIENT_INVOICE"

    # Verify booking financials include persisted revenue charge
    booking_response = client.get("/api/bookings/BL-001")
    assert booking_response.status_code == 200
    booking = booking_response.json()
    assert Decimal(booking["total_revenue"]) == Decimal("1000.00")
    assert Decimal(booking["total_costs"]) == Decimal("0.00")
    assert Decimal(booking["margin"]) == Decimal("1000.00")
    assert booking["client_name"] == "Client A"


def test_confirm_reprocess_replaces_existing_projection_for_same_document(
    client: TestClient, pending_document
) -> None:
    first_response = client.post(
        "/api/invoices/confirm",
        json={
            "document_id": str(pending_document.id),
            "document_type": "CLIENT_INVOICE",
            "ai_model": "gemini-3-pro",
            "raw_json": "{\"document_type\":\"CLIENT_INVOICE\"}",
            "overall_confidence": "HIGH",
            "invoice_number": "INV-REPROCESS-1",
            "invoice_date": "2024-01-15",
            "issuer_name": "Our Company",
            "issuer_nif": "B00000000",
            "recipient_name": "Client A",
            "recipient_nif": "C11111111",
            "bl_references": ["BL-REPROCESS-1"],
            "charges": [
                {
                    "bl_reference": "BL-REPROCESS-1",
                    "description": "Original revenue",
                    "category": "FREIGHT",
                    "amount": "1000.00",
                }
            ],
            "totals": {"tax_amount": "210.00", "total": "1210.00"},
            "shipping_details": {},
        },
    )
    assert first_response.status_code == 200
    first_invoice_id = first_response.json()["invoice_id"]

    second_response = client.post(
        "/api/invoices/confirm",
        json={
            "document_id": str(pending_document.id),
            "document_type": "CLIENT_INVOICE",
            "ai_model": "gemini-3-pro",
            "raw_json": "{\"document_type\":\"CLIENT_INVOICE\"}",
            "overall_confidence": "HIGH",
            "invoice_number": "INV-REPROCESS-1",
            "invoice_date": "2024-01-15",
            "issuer_name": "Our Company",
            "issuer_nif": "B00000000",
            "recipient_name": "Client A",
            "recipient_nif": "C11111111",
            "bl_references": ["BL-REPROCESS-1"],
            "charges": [
                {
                    "bl_reference": "BL-REPROCESS-1",
                    "description": "Reprocessed revenue",
                    "category": "FREIGHT",
                    "amount": "2000.00",
                }
            ],
            "totals": {"tax_amount": "420.00", "total": "2420.00"},
            "shipping_details": {},
        },
    )

    assert second_response.status_code == 200
    second_invoice_id = second_response.json()["invoice_id"]
    assert second_invoice_id is not None
    assert second_invoice_id != first_invoice_id

    booking_response = client.get("/api/bookings/BL-REPROCESS-1")
    assert booking_response.status_code == 200
    booking = booking_response.json()
    assert Decimal(booking["total_revenue"]) == Decimal("2000.00")
    assert Decimal(booking["total_costs"]) == Decimal("0.00")
    assert booking["revenue_charge_count"] == 1
    assert booking["revenue_charges"][0]["description"] == "Reprocessed revenue"


def test_confirm_document_validation_error(client: TestClient, pending_document) -> None:
    response = client.post(
        "/api/invoices/confirm",
        json={
            "document_id": str(pending_document.id),
            "document_type": "CLIENT_INVOICE",
            "ai_model": "gemini-3-pro",
            "raw_json": "{}",
            "invoice_number": "INV-101",
            "invoice_date": "2024-01-15",
            "recipient_name": "Client A",
            "recipient_nif": "C11111111",
            "charges": [],
        },
    )

    assert response.status_code == 400
    assert "charge" in response.json()["detail"].lower()

def test_confirm_document_invalid_document_type_returns_422(
    client: TestClient, pending_document
) -> None:
    response = client.post(
        "/api/invoices/confirm",
        json={
            "document_id": str(pending_document.id),
            "document_type": "INVALID_TYPE",
            "ai_model": "gemini-3-pro",
            "raw_json": "{\"document_type\":\"INVALID_TYPE\"}",
            "overall_confidence": "HIGH",
            "invoice_number": "INV-102",
            "invoice_date": "2024-01-15",
            "issuer_name": "Our Company",
            "issuer_nif": "B00000000",
            "recipient_name": "Client A",
            "recipient_nif": "C11111111",
            "bl_references": ["BL-001"],
            "charges": [
                {
                    "bl_reference": "BL-001",
                    "description": "Ocean Freight",
                    "category": "FREIGHT",
                    "amount": "1000.00",
                }
            ],
            "totals": {"tax_amount": "210.00", "total": "1210.00"},
            "shipping_details": {},
        },
    )

    assert response.status_code == 422
    assert "document_type" in str(response.json()["detail"])


def test_confirm_document_invalid_invoice_date_returns_422(
    client: TestClient, pending_document
) -> None:
    response = client.post(
        "/api/invoices/confirm",
        json={
            "document_id": str(pending_document.id),
            "document_type": "CLIENT_INVOICE",
            "ai_model": "gemini-3-pro",
            "raw_json": "{\"document_type\":\"CLIENT_INVOICE\"}",
            "overall_confidence": "HIGH",
            "invoice_number": "INV-103",
            "invoice_date": "15/01/2024",
            "issuer_name": "Our Company",
            "issuer_nif": "B00000000",
            "recipient_name": "Client A",
            "recipient_nif": "C11111111",
            "bl_references": ["BL-001"],
            "charges": [
                {
                    "bl_reference": "BL-001",
                    "description": "Ocean Freight",
                    "category": "FREIGHT",
                    "amount": "1000.00",
                }
            ],
            "totals": {"tax_amount": "210.00", "total": "1210.00"},
            "shipping_details": {},
        },
    )

    assert response.status_code == 422
    assert "invoice_date" in str(response.json()["detail"])


def test_confirm_document_invalid_provider_type_returns_422(
    client: TestClient, pending_document
) -> None:
    response = client.post(
        "/api/invoices/confirm",
        json={
            "document_id": str(pending_document.id),
            "document_type": "PROVIDER_INVOICE",
            "ai_model": "gemini-3-pro",
            "raw_json": "{\"document_type\":\"PROVIDER_INVOICE\"}",
            "overall_confidence": "HIGH",
            "invoice_number": "INV-200",
            "invoice_date": "2024-01-20",
            "issuer_name": "Provider A",
            "issuer_nif": "P22222222",
            "recipient_name": "Our Company",
            "recipient_nif": "B00000000",
            "provider_type": "INVALID_PROVIDER",
            "bl_references": ["BL-200"],
            "charges": [
                {
                    "bl_reference": "BL-200",
                    "description": "Ocean Freight",
                    "category": "FREIGHT",
                    "amount": "1000.00",
                }
            ],
            "totals": {"tax_amount": "210.00", "total": "1210.00"},
        },
    )

    assert response.status_code == 422
    assert "provider_type" in str(response.json()["detail"])


def test_confirm_document_invalid_charge_category_returns_422(
    client: TestClient, pending_document
) -> None:
    response = client.post(
        "/api/invoices/confirm",
        json={
            "document_id": str(pending_document.id),
            "document_type": "PROVIDER_INVOICE",
            "ai_model": "gemini-3-pro",
            "raw_json": "{\"document_type\":\"PROVIDER_INVOICE\"}",
            "overall_confidence": "HIGH",
            "invoice_number": "INV-201",
            "invoice_date": "2024-01-20",
            "issuer_name": "Provider A",
            "issuer_nif": "P22222222",
            "recipient_name": "Our Company",
            "recipient_nif": "B00000000",
            "provider_type": "SHIPPING",
            "bl_references": ["BL-201"],
            "charges": [
                {
                    "bl_reference": "BL-201",
                    "description": "Ocean Freight",
                    "category": "INVALID_CATEGORY",
                    "amount": "1000.00",
                }
            ],
            "totals": {"tax_amount": "210.00", "total": "1210.00"},
        },
    )

    assert response.status_code == 422
    assert "category" in str(response.json()["detail"])


@pytest.fixture
def sample_persisted_invoices(db_session):
    """Create persisted client/provider invoices for search endpoint tests."""
    client_repo = SqlAlchemyClientRepository(db_session)
    provider_repo = SqlAlchemyProviderRepository(db_session)
    invoice_repo = SqlAlchemyInvoiceRepository(db_session)

    client = Client.create(nif="C12345678", name="Acme Trading")
    provider = Provider.create(
        nif="P12345678",
        provider_type=ProviderType.CARRIER,
        name="Ocean Carrier",
    )
    client_repo.save(client)
    provider_repo.save(provider)

    client_invoice = ClientInvoice.create(
        invoice_number="INV-C-001",
        client_id=client.id,
        invoice_date=date(2024, 1, 10),
        bl_reference="BL-SEARCH-001",
        total_amount=Money(Decimal("1000.00")),
        tax_amount=Money(Decimal("0.00")),
    )
    provider_invoice = ProviderInvoice.create(
        invoice_number="INV-P-001",
        provider_id=provider.id,
        provider_type=ProviderType.CARRIER,
        invoice_date=date(2024, 1, 12),
        bl_references=["BL-SEARCH-001", "BL-SEARCH-002"],
        total_amount=Money(Decimal("650.00")),
        tax_amount=Money(Decimal("0.00")),
    )
    invoice_repo.save_client_invoice(client_invoice)
    invoice_repo.save_provider_invoice(provider_invoice)
    return client_invoice, provider_invoice


def test_list_invoices_returns_client_and_provider_rows(
    client: TestClient, sample_persisted_invoices
) -> None:
    """Test invoice search returns unified rows across both invoice types."""
    _ = sample_persisted_invoices
    response = client.get("/api/invoices")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    invoice_types = {row["invoice_type"] for row in payload["invoices"]}
    assert invoice_types == {"CLIENT_INVOICE", "PROVIDER_INVOICE"}


def test_list_invoices_filters_by_number_party_and_type(
    client: TestClient, sample_persisted_invoices
) -> None:
    """Test invoice search filters by number/party/type are applied."""
    _ = sample_persisted_invoices
    response = client.get(
        "/api/invoices?invoice_number=INV-P&party=ocean&invoice_type=PROVIDER_INVOICE"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    item = payload["invoices"][0]
    assert item["invoice_number"] == "INV-P-001"
    assert item["party_name"] == "Ocean Carrier"
    assert item["booking_references"] == ["BL-SEARCH-001", "BL-SEARCH-002"]
    assert item["total_amount"] == "650.00"


def test_list_invoices_invalid_date_range_returns_400(client: TestClient) -> None:
    """Test invoice search rejects invalid date range."""
    response = client.get("/api/invoices?date_from=2024-02-01&date_to=2024-01-01")
    assert response.status_code == 400
    assert "date_from cannot be greater than date_to" in response.json()["detail"]
