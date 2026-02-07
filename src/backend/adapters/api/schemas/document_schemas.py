"""Pydantic schemas for document API."""

from datetime import datetime
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

    # Error info
    error_message: str | None
    error_retryable: bool | None


class ListDocumentsResponse(BaseModel):
    """Response for list documents endpoint."""

    documents: list[DocumentListItem]
    total: int


class ListDocumentsParams(BaseModel):
    """Query parameters for list documents endpoint."""

    status: str | None = Field(None, description="Filter by status (PENDING, PROCESSING, etc.)")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of documents to return")
