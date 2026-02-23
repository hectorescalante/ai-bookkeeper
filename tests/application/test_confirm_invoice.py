"""Tests for ConfirmInvoiceUseCase."""

from unittest.mock import MagicMock

import pytest

from backend.application.dtos.invoice_dtos import ConfirmInvoiceRequest, SaveChargeInput
from backend.application.use_cases.confirm_invoice import ConfirmInvoiceUseCase
from backend.domain.entities.booking import Booking
from backend.domain.entities.document import Document
from backend.domain.entities.invoice import ClientInvoice, ProviderInvoice
from backend.domain.entities.party import Client, Provider
from backend.domain.enums import DocumentType, ProcessingStatus, ProviderType
from backend.domain.value_objects import FileHash, Money


def _make_document() -> Document:
    return Document.create(
        filename="invoice.pdf",
        file_hash=FileHash.sha256("doc-hash"),
        storage_path="/tmp/invoice.pdf",
    )


def _base_request(document_id, document_type: str = "CLIENT_INVOICE") -> ConfirmInvoiceRequest:
    return ConfirmInvoiceRequest(
        document_id=document_id,
        document_type=document_type,
        ai_model="gemini-3-pro",
        raw_json='{"ok": true}',
        overall_confidence="HIGH",
        invoice_number="INV-001",
        invoice_date="2024-01-15",
        issuer_name="Our Company",
        issuer_nif="B00000000",
        recipient_name="Client A",
        recipient_nif="C11111111",
        provider_type="SHIPPING",
        bl_references=["BL-001"],
        charges=[
            SaveChargeInput(
                bl_reference="BL-001",
                description="Ocean Freight",
                category="FREIGHT",
                amount="1000.00",
                container=None,
            )
        ],
        totals={"tax_amount": "210.00", "total": "1210.00"},
    )


def test_confirm_client_invoice_persists_invoice_booking_and_document() -> None:
    document = _make_document()

    document_repo = MagicMock()
    document_repo.find_by_id.return_value = document
    booking_repo = MagicMock()
    booking_repo.find_or_create.return_value = Booking.create("BL-001")
    invoice_repo = MagicMock()
    invoice_repo.find_client_invoice.return_value = None
    client_repo = MagicMock()
    client_repo.find_by_nif.return_value = None
    provider_repo = MagicMock()

    use_case = ConfirmInvoiceUseCase(
        document_repo=document_repo,
        booking_repo=booking_repo,
        invoice_repo=invoice_repo,
        client_repo=client_repo,
        provider_repo=provider_repo,
    )

    request = _base_request(document.id, "CLIENT_INVOICE")
    response = use_case.execute(request)

    assert response.document_id == document.id
    assert response.document_type == "CLIENT_INVOICE"
    assert response.status == "PROCESSED"
    assert response.invoice_id is not None
    assert response.booking_ids == ["BL-001"]

    client_repo.save.assert_called_once()
    invoice_repo.save_client_invoice.assert_called_once()
    booking_repo.save.assert_called_once()
    document_repo.update.assert_called()
    assert document.status == ProcessingStatus.PROCESSED
    assert document.document_type == DocumentType.CLIENT_INVOICE

    saved_invoice = invoice_repo.save_client_invoice.call_args[0][0]
    assert isinstance(saved_invoice, ClientInvoice)
    assert saved_invoice.invoice_number == "INV-001"
    assert len(saved_invoice.charges) == 1


def test_confirm_provider_invoice_multi_booking_persists_costs() -> None:
    document = _make_document()

    document_repo = MagicMock()
    document_repo.find_by_id.return_value = document

    booking_map = {
        "BL-001": Booking.create("BL-001"),
        "BL-002": Booking.create("BL-002"),
    }

    booking_repo = MagicMock()
    booking_repo.find_or_create.side_effect = lambda bl: booking_map[bl]
    invoice_repo = MagicMock()
    invoice_repo.find_provider_invoice.return_value = None
    client_repo = MagicMock()
    provider_repo = MagicMock()
    provider_repo.find_by_nif.return_value = Provider.create(
        nif="P12345678",
        provider_type=ProviderType.CARRIER,
        name="Carrier Inc",
    )

    use_case = ConfirmInvoiceUseCase(
        document_repo=document_repo,
        booking_repo=booking_repo,
        invoice_repo=invoice_repo,
        client_repo=client_repo,
        provider_repo=provider_repo,
    )

    request = ConfirmInvoiceRequest(
        document_id=document.id,
        document_type="PROVIDER_INVOICE",
        ai_model="gemini-3-pro",
        raw_json='{"ok": true}',
        overall_confidence="HIGH",
        invoice_number="PINV-001",
        invoice_date="2024-01-15",
        issuer_name="Carrier Inc",
        issuer_nif="P12345678",
        recipient_name="Our Company",
        recipient_nif="B00000000",
        provider_type="CARRIER",
        bl_references=["BL-001", "BL-002"],
        charges=[
            SaveChargeInput(
                bl_reference="BL-001",
                description="Leg 1",
                category="TRANSPORT",
                amount="400.00",
            ),
            SaveChargeInput(
                bl_reference="BL-002",
                description="Leg 2",
                category="TRANSPORT",
                amount="600.00",
            ),
        ],
        totals={"tax_amount": "210.00", "total": "1210.00"},
    )

    response = use_case.execute(request)

    assert response.document_type == "PROVIDER_INVOICE"
    assert response.booking_ids == ["BL-001", "BL-002"]
    assert response.invoice_id is not None
    invoice_repo.save_provider_invoice.assert_called_once()
    assert booking_repo.save.call_count == 2

    saved_invoice = invoice_repo.save_provider_invoice.call_args[0][0]
    assert isinstance(saved_invoice, ProviderInvoice)
    assert len(saved_invoice.charges) == 2


def test_confirm_other_document_marks_processed_without_invoice() -> None:
    document = _make_document()

    document_repo = MagicMock()
    document_repo.find_by_id.return_value = document

    use_case = ConfirmInvoiceUseCase(
        document_repo=document_repo,
        booking_repo=MagicMock(),
        invoice_repo=MagicMock(),
        client_repo=MagicMock(),
        provider_repo=MagicMock(),
    )

    request = ConfirmInvoiceRequest(
        document_id=document.id,
        document_type="OTHER",
        ai_model="gemini-3-pro",
        raw_json='{"document_type":"OTHER"}',
    )

    response = use_case.execute(request)

    assert response.document_type == "OTHER"
    assert response.invoice_id is None
    assert response.booking_ids == []
    assert document.status == ProcessingStatus.PROCESSED
    document_repo.update.assert_called_once()


def test_confirm_duplicate_client_invoice_raises_error() -> None:
    document = _make_document()

    document_repo = MagicMock()
    document_repo.find_by_id.return_value = document
    booking_repo = MagicMock()
    invoice_repo = MagicMock()
    client_repo = MagicMock()
    provider_repo = MagicMock()

    existing_client = Client.create(nif="C11111111", name="Client A")
    client_repo.find_by_nif.return_value = existing_client
    invoice_repo.find_client_invoice.return_value = ClientInvoice.create(
        invoice_number="INV-001",
        client_id=existing_client.id,
        invoice_date=document.created_at.date(),
        bl_reference="BL-001",
        total_amount=Money.from_float(1000.0),
        tax_amount=Money.from_float(210.0),
    )

    use_case = ConfirmInvoiceUseCase(
        document_repo=document_repo,
        booking_repo=booking_repo,
        invoice_repo=invoice_repo,
        client_repo=client_repo,
        provider_repo=provider_repo,
    )

    request = _base_request(document.id, "CLIENT_INVOICE")
    with pytest.raises(ValueError, match="already exists"):
        use_case.execute(request)
