"""Documents API routes."""
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from backend.adapters.api.routes.invoices import ProcessDocumentResponse
from backend.adapters.api.schemas import (
    DocumentListItem,
    FetchEmailsRequest,
    FetchEmailsResponse,
    ListDocumentsResponse,
)
from backend.application.dtos import FetchEmailsRequest as FetchEmailsRequestDto
from backend.application.dtos import (
    ListDocumentsRequest,
    ProcessInvoiceRequest,
    ProcessInvoiceResponse,
)
from backend.application.use_cases import (
    FetchEmailsUseCase,
    ListDocumentsUseCase,
    ProcessInvoiceUseCase,
)
from backend.config.dependencies import (
    get_document_repository,
    get_fetch_emails_use_case,
    get_list_documents_use_case,
    get_process_invoice_use_case,
)
from backend.ports.output.repositories import DocumentRepository

router = APIRouter(prefix="/api/documents", tags=["documents"])
DocumentStatusFilter = Literal["PENDING", "PROCESSING", "PROCESSED", "ERROR"]
DocumentTypeFilter = Literal["CLIENT_INVOICE", "PROVIDER_INVOICE", "OTHER"]


@router.get("", response_model=ListDocumentsResponse, status_code=200)
def list_documents(
    status: Annotated[
        DocumentStatusFilter | None,
        Query(description="Filter by status"),
    ] = None,
    document_type: Annotated[
        DocumentTypeFilter | None,
        Query(description="Filter by document type"),
    ] = None,
    date_from: Annotated[date | None, Query(description="Date from (ISO)")] = None,
    date_to: Annotated[date | None, Query(description="Date to (ISO)")] = None,
    party: Annotated[str | None, Query(description="Filter by client/provider name")] = None,
    booking: Annotated[str | None, Query(description="Filter by booking reference")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Maximum results")] = 100,
    use_case: ListDocumentsUseCase = Depends(get_list_documents_use_case),
) -> ListDocumentsResponse:
    """List documents with optional status filtering."""
    try:
        dto_request = ListDocumentsRequest(
            status=status,
            document_type=document_type,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            party=party,
            booking=booking,
            limit=limit,
        )
        documents = use_case.execute(dto_request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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
                invoice_number=doc.invoice_number,
                party_name=doc.party_name,
                booking_references=doc.booking_references or [],
                total_amount=doc.total_amount,
                file_url=doc.file_url,
            )
            for doc in documents
        ],
        total=len(documents),
    )


@router.get("/{document_id}/file", response_class=FileResponse, status_code=200)
def get_document_file(
    document_id: UUID,
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> FileResponse:
    """Download source PDF for a document when available."""
    document = document_repo.find_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
    if not document.storage_path:
        raise HTTPException(status_code=404, detail="Document file is not available")

    file_path = Path(document.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file does not exist")

    return FileResponse(
        path=file_path,
        filename=document.filename,
        media_type="application/pdf",
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


def _build_process_response(result: ProcessInvoiceResponse) -> ProcessDocumentResponse:
    return ProcessDocumentResponse(
        document_id=result.document_id,
        document_type=result.document_type,
        document_type_confidence=result.document_type_confidence,
        ai_model=result.ai_model,
        raw_json=result.raw_json,
        invoice_number=result.invoice_number,
        invoice_date=result.invoice_date,
        issuer_name=result.issuer_name,
        issuer_nif=result.issuer_nif,
        recipient_name=result.recipient_name,
        recipient_nif=result.recipient_nif,
        provider_type=result.provider_type,
        currency_valid=result.currency_valid,
        currency_detected=result.currency_detected,
        bl_references=result.bl_references,
        charges=result.charges,
        totals=result.totals,
        extraction_notes=result.extraction_notes,
        overall_confidence=result.overall_confidence,
        warnings=result.warnings,
        errors=result.errors,
    )


def _raise_process_http_error(exc: ValueError) -> NoReturn:
    detail = str(exc)
    lowered = detail.lower()
    if "not configured" in lowered or "not found" in lowered:
        raise HTTPException(status_code=400, detail=detail) from exc
    if "invalid" in lowered and "key" in lowered:
        raise HTTPException(status_code=401, detail=detail) from exc
    if "rate limit" in lowered:
        raise HTTPException(status_code=429, detail=detail) from exc
    if "timed out" in lowered:
        raise HTTPException(status_code=504, detail=detail) from exc
    raise HTTPException(status_code=400, detail=detail) from exc


@router.post("/{document_id}/retry", response_model=ProcessDocumentResponse, status_code=200)
def retry_document(
    document_id: UUID,
    use_case: Annotated[ProcessInvoiceUseCase, Depends(get_process_invoice_use_case)],
) -> ProcessDocumentResponse:
    """Retry processing a document in ERROR status."""
    try:
        result = use_case.execute(ProcessInvoiceRequest(document_id=document_id))
        return _build_process_response(result)
    except ValueError as exc:
        _raise_process_http_error(exc)


@router.post("/{document_id}/reprocess", response_model=ProcessDocumentResponse, status_code=200)
def reprocess_document(
    document_id: UUID,
    use_case: Annotated[ProcessInvoiceUseCase, Depends(get_process_invoice_use_case)],
) -> ProcessDocumentResponse:
    """Reprocess a previously processed document."""
    try:
        result = use_case.execute(
            ProcessInvoiceRequest(document_id=document_id, allow_processed=True)
        )
        return _build_process_response(result)
    except ValueError as exc:
        _raise_process_http_error(exc)
