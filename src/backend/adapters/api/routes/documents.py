"""Documents API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.adapters.api.schemas import (
    DocumentListItem,
    ListDocumentsResponse,
)
from backend.application.dtos import ListDocumentsRequest
from backend.application.use_cases import ListDocumentsUseCase
from backend.config.dependencies import get_list_documents_use_case

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=ListDocumentsResponse, status_code=200)
def list_documents(
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Maximum results")] = 100,
    use_case: Annotated[ListDocumentsUseCase, Depends(get_list_documents_use_case)] = ...,
) -> ListDocumentsResponse:
    """List documents with optional status filtering."""
    # Map query params to DTO
    dto_request = ListDocumentsRequest(
        status=status,
        limit=limit,
    )

    # Execute use case
    documents = use_case.execute(dto_request)

    # Map DTOs to Pydantic
    return ListDocumentsResponse(
        documents=[
            DocumentListItem(
                id=doc.id,
                filename=doc.filename,
                status=doc.status,
                document_type=doc.document_type,
                created_at=doc.created_at,
                processed_at=doc.processed_at,
                email_sender=doc.email_sender,
                email_subject=doc.email_subject,
                error_message=doc.error_message,
                error_retryable=doc.error_retryable,
            )
            for doc in documents
        ],
        total=len(documents),
    )
