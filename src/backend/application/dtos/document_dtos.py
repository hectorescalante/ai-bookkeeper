"""DTOs for document use cases."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class DocumentListItem:
    """Document summary for list view."""

    id: UUID
    filename: str
    status: str
    document_type: str | None
    created_at: datetime
    processed_at: datetime | None

    # Email info (if from email)
    email_sender: str | None
    email_subject: str | None
    pdf_count_in_email: int | None

    # Error info (if error)
    error_message: str | None
    error_retryable: bool | None
    # Processed history metadata
    invoice_number: str | None = None
    party_name: str | None = None
    booking_references: list[str] | None = None
    total_amount: Decimal | None = None
    file_url: str | None = None
    manually_edited_fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ListDocumentsRequest:
    """Request to list documents by status."""

    status: str | None = None
    limit: int = 100
    document_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    party: str | None = None
    booking: str | None = None


@dataclass(frozen=True)
class FetchEmailsRequest:
    """Request to fetch Outlook emails with PDF attachments."""

    max_messages: int = 25


@dataclass(frozen=True)
class FetchEmailsResponse:
    """Summary result for an email fetch operation."""

    scanned_messages: int
    pdf_attachments_found: int
    imported_documents: int
    duplicate_documents: int
