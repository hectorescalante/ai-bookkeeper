"""Documents API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.adapters.api.schemas import (
    DocumentListItem,
    FetchEmailsRequest,
    FetchEmailsResponse,
    ListDocumentsResponse,
)
from backend.application.dtos import (
    FetchEmailsRequest as FetchEmailsRequestDto,
)
from backend.application.dtos import (
    ListDocumentsRequest,
)
from backend.application.use_cases import FetchEmailsUseCase, ListDocumentsUseCase
from backend.config.dependencies import (
    get_fetch_emails_use_case,
    get_list_documents_use_case,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=ListDocumentsResponse, status_code=200)
def list_documents(
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Maximum results")] = 100,
    use_case: ListDocumentsUseCase = Depends(get_list_documents_use_case),
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


@router.post("/fetch", response_model=FetchEmailsResponse, status_code=200)
def fetch_emails(
    request: FetchEmailsRequest,
    use_case: FetchEmailsUseCase = Depends(get_fetch_emails_use_case),
) -> FetchEmailsResponse:
    """Fetch unread Outlook emails and import PDF attachments as documents."""
    try:
        result = use_case.execute(FetchEmailsRequestDto(max_messages=request.max_messages))
        return FetchEmailsResponse(
            scanned_messages=result.scanned_messages,
            pdf_attachments_found=result.pdf_attachments_found,
            imported_documents=result.imported_documents,
            duplicate_documents=result.duplicate_documents,
        )
    except ValueError as exc:
        detail = str(exc)
        lowered = detail.lower()
        if "not connected" in lowered or "authentication failed" in lowered:
            raise HTTPException(status_code=400, detail=detail) from exc
        if "rate limit" in lowered:
            raise HTTPException(status_code=429, detail=detail) from exc
        raise HTTPException(status_code=502, detail=detail) from exc
