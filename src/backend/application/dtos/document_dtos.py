"""DTOs for document use cases."""

from dataclasses import dataclass
from datetime import datetime
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

    # Error info (if error)
    error_message: str | None
    error_retryable: bool | None


@dataclass(frozen=True)
class ListDocumentsRequest:
    """Request to list documents by status."""

    status: str | None = None
    limit: int = 100


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
