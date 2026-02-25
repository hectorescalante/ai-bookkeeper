"""Integration tests for invoice processing API endpoints."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.adapters.persistence.repositories.document_repository import (
    SqlAlchemyDocumentRepository,
)
from backend.domain.entities.document import Document
from backend.domain.value_objects import FileHash


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
