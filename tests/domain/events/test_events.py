"""Tests for domain events."""

from datetime import datetime
from uuid import uuid4

from backend.domain.enums import DocumentType, ErrorType
from backend.domain.events import (
    BookingUpdated,
    DocumentReceived,
    ExtractionFailed,
    InvoiceProcessed,
)
from backend.domain.value_objects import Money


class TestDocumentReceived:
    """Tests for DocumentReceived event."""

    def test_create_document_received(self) -> None:
        """Test creating DocumentReceived event."""
        doc_id = uuid4()
        event = DocumentReceived(
            document_id=doc_id,
            filename="invoice.pdf",
        )
        assert event.document_id == doc_id
        assert event.filename == "invoice.pdf"
        assert event.email_message_id is None
        assert event.occurred_at is not None

    def test_document_received_from_email(self) -> None:
        """Test creating event with email reference."""
        doc_id = uuid4()
        event = DocumentReceived(
            document_id=doc_id,
            filename="invoice.pdf",
            email_message_id="MSG12345",
        )
        assert event.email_message_id == "MSG12345"

    def test_document_received_with_timestamp(self) -> None:
        """Test creating event with specific timestamp."""
        doc_id = uuid4()
        ts = datetime(2024, 1, 15, 10, 30, 0)
        event = DocumentReceived(
            document_id=doc_id,
            filename="invoice.pdf",
            occurred_at=ts,
        )
        assert event.occurred_at == ts


class TestInvoiceProcessed:
    """Tests for InvoiceProcessed event."""

    def test_create_invoice_processed(self) -> None:
        """Test creating InvoiceProcessed event."""
        invoice_id = uuid4()
        doc_id = uuid4()
        event = InvoiceProcessed(
            document_id=doc_id,
            invoice_id=invoice_id,
            document_type=DocumentType.CLIENT_INVOICE,
            bl_references=("BL-001",),
            total_amount=Money.from_float(1210.00),
        )
        assert event.invoice_id == invoice_id
        assert event.document_id == doc_id
        assert event.document_type == DocumentType.CLIENT_INVOICE
        assert event.bl_references == ("BL-001",)
        assert event.total_amount == Money.from_float(1210.00)
        assert event.occurred_at is not None

    def test_invoice_processed_multiple_bls(self) -> None:
        """Test event with multiple BL references."""
        invoice_id = uuid4()
        doc_id = uuid4()
        event = InvoiceProcessed(
            document_id=doc_id,
            invoice_id=invoice_id,
            document_type=DocumentType.PROVIDER_INVOICE,
            bl_references=("BL-001", "BL-002", "BL-003"),
            total_amount=Money.from_float(3000.00),
        )
        assert len(event.bl_references) == 3


class TestExtractionFailed:
    """Tests for ExtractionFailed event."""

    def test_create_extraction_failed(self) -> None:
        """Test creating ExtractionFailed event."""
        doc_id = uuid4()
        event = ExtractionFailed(
            document_id=doc_id,
            error_type=ErrorType.AI_TIMEOUT,
            error_message="AI processing timed out",
        )
        assert event.document_id == doc_id
        assert event.error_type == ErrorType.AI_TIMEOUT
        assert event.error_message == "AI processing timed out"
        assert event.occurred_at is not None

    def test_extraction_failed_duplicate(self) -> None:
        """Test extraction failed due to duplicate."""
        doc_id = uuid4()
        event = ExtractionFailed(
            document_id=doc_id,
            error_type=ErrorType.DUPLICATE_DOCUMENT,
            error_message="Document already imported",
        )
        assert event.error_type == ErrorType.DUPLICATE_DOCUMENT


class TestBookingUpdated:
    """Tests for BookingUpdated event."""

    def test_create_booking_updated(self) -> None:
        """Test creating BookingUpdated event."""
        invoice_id = uuid4()
        event = BookingUpdated(
            booking_id="BL-001",
            invoice_id=invoice_id,
            new_total_revenue=Money.from_float(1500.00),
            new_total_costs=Money.from_float(1000.00),
            new_margin=Money.from_float(500.00),
        )
        assert event.booking_id == "BL-001"
        assert event.invoice_id == invoice_id
        assert event.new_total_revenue == Money.from_float(1500.00)
        assert event.new_total_costs == Money.from_float(1000.00)
        assert event.new_margin == Money.from_float(500.00)
        assert event.occurred_at is not None

    def test_booking_updated_negative_margin(self) -> None:
        """Test event with negative margin (costs > revenue)."""
        invoice_id = uuid4()
        event = BookingUpdated(
            booking_id="BL-001",
            invoice_id=invoice_id,
            new_total_revenue=Money.from_float(800.00),
            new_total_costs=Money.from_float(1000.00),
            new_margin=Money.from_float(-200.00),
        )
        assert event.new_margin == Money.from_float(-200.00)
        assert event.new_margin.is_negative()
