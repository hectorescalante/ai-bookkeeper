"""Domain events for event-driven design."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from backend.domain.enums import DocumentType, ErrorType
from backend.domain.value_objects import Money


@dataclass(frozen=True)
class DocumentReceived:
    """Event raised when a new PDF document is downloaded from email.

    This event indicates a new document has been added to the system
    and is ready for processing.
    """

    document_id: UUID
    filename: str
    email_message_id: str | None = None
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class InvoiceProcessed:
    """Event raised when AI extraction completes successfully.

    This event indicates an invoice has been extracted and classified,
    and its charges have been attributed to bookings.
    """

    document_id: UUID
    invoice_id: UUID
    document_type: DocumentType
    bl_references: tuple[str, ...]
    total_amount: Money
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class ExtractionFailed:
    """Event raised when AI extraction fails.

    This event indicates the document could not be processed,
    either due to an error or validation failure.
    """

    document_id: UUID
    error_type: ErrorType
    error_message: str
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class BookingUpdated:
    """Event raised when charges are added to a booking.

    This event indicates a booking's financial data has changed
    and margins/commissions have been recalculated.
    """

    booking_id: str
    invoice_id: UUID
    new_total_revenue: Money
    new_total_costs: Money
    new_margin: Money
    occurred_at: datetime = field(default_factory=datetime.now)


# Type alias for any domain event
DomainEvent = DocumentReceived | InvoiceProcessed | ExtractionFailed | BookingUpdated
