"""Pydantic schemas for document API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentListItem(BaseModel):
    """Document summary for list view."""

    id: UUID
    filename: str
    status: str
    document_type: str | None
    created_at: datetime
    processed_at: datetime | None

    # Email info
    email_sender: str | None
    email_subject: str | None
    pdf_count_in_email: int | None

    # Error info
    error_message: str | None
    error_retryable: bool | None
    # Processed history metadata
    invoice_number: str | None
    party_name: str | None
    booking_references: list[str]
    total_amount: Decimal | None
    file_url: str | None
    manually_edited_fields: list[str]


class ListDocumentsResponse(BaseModel):
    """Response for list documents endpoint."""

    documents: list[DocumentListItem]
    total: int


class ListDocumentsParams(BaseModel):
    """Query parameters for list documents endpoint."""

    status: str | None = Field(None, description="Filter by status (PENDING, PROCESSING, etc.)")
    document_type: str | None = Field(
        None,
        description="Filter by document type (CLIENT_INVOICE, PROVIDER_INVOICE, OTHER)",
    )
    date_from: str | None = Field(None, description="Filter by date from (ISO format)")
    date_to: str | None = Field(None, description="Filter by date to (ISO format)")
    party: str | None = Field(
        None,
        description="Filter by client/provider name (contains, case-insensitive)",
    )
    booking: str | None = Field(
        None,
        description="Filter by booking reference (contains, case-insensitive)",
    )
    limit: int = Field(100, ge=1, le=500, description="Maximum number of documents to return")


class FetchEmailsRequest(BaseModel):
    """Request payload for fetching Outlook emails."""

    max_messages: int = Field(
        25,
        ge=1,
        le=100,
        description="Maximum unread messages to scan in Outlook inbox",
    )


class FetchEmailsResponse(BaseModel):
    """Summary response for a fetch emails operation."""

    scanned_messages: int
    pdf_attachments_found: int
    imported_documents: int
    duplicate_documents: int
