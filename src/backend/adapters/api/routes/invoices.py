"""Invoice processing API routes."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.application.dtos.invoice_dtos import (
    ConfirmInvoiceRequest,
    ListInvoicesRequest,
    ProcessInvoiceRequest,
    SaveChargeInput,
)
from backend.application.use_cases.confirm_invoice import ConfirmInvoiceUseCase
from backend.application.use_cases.list_invoices import ListInvoicesUseCase
from backend.application.use_cases.process_invoice import ProcessInvoiceUseCase
from backend.config.dependencies import (
    get_confirm_invoice_use_case,
    get_list_invoices_use_case,
    get_process_invoice_use_case,
)
from backend.domain.enums import ChargeCategory, ProviderType

router = APIRouter(prefix="/api/invoices", tags=["invoices"])
InvoiceDocumentType = Literal["CLIENT_INVOICE", "PROVIDER_INVOICE", "OTHER"]
InvoiceSearchType = Literal["CLIENT_INVOICE", "PROVIDER_INVOICE"]


class ProcessDocumentRequest(BaseModel):
    """Request to process a document with AI extraction."""

    document_id: UUID = Field(..., description="ID of the document to process")


class ProcessDocumentResponse(BaseModel):
    """Response with extracted invoice data for user preview."""

    document_id: UUID
    document_type: InvoiceDocumentType
    document_type_confidence: str
    ai_model: str
    raw_json: str

    # Extracted fields
    invoice_number: str | None = None
    invoice_date: str | None = None
    issuer_name: str | None = None
    issuer_nif: str | None = None
    recipient_name: str | None = None
    recipient_nif: str | None = None
    provider_type: str | None = None
    currency_valid: bool = True
    currency_detected: str = "EUR"

    bl_references: list[dict[str, Any]] = Field(default_factory=list)
    charges: list[dict[str, Any]] = Field(default_factory=list)
    totals: dict[str, Any] = Field(default_factory=dict)

    extraction_notes: str | None = None
    overall_confidence: str = "HIGH"
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ConfirmChargeRequest(BaseModel):
    """Single reviewed charge line."""

    bl_reference: str | None = None
    description: str
    category: ChargeCategory
    amount: str | float | int
    container: str | None = None


class ConfirmDocumentRequest(BaseModel):
    """Request to confirm reviewed data and persist invoice."""

    document_id: UUID
    document_type: InvoiceDocumentType
    ai_model: str
    raw_json: str
    overall_confidence: str = "HIGH"
    manually_edited_fields: list[str] = Field(default_factory=list)

    invoice_number: str | None = None
    invoice_date: date | None = None
    issuer_name: str | None = None
    issuer_nif: str | None = None
    recipient_name: str | None = None
    recipient_nif: str | None = None
    provider_type: ProviderType | None = None
    currency_valid: bool = True
    currency_detected: str = "EUR"

    bl_references: list[str | dict[str, Any]] = Field(default_factory=list)
    charges: list[ConfirmChargeRequest] = Field(default_factory=list)
    totals: dict[str, Any] = Field(default_factory=dict)
    shipping_details: dict[str, Any] = Field(default_factory=dict)


class ConfirmDocumentResponse(BaseModel):
    """Response after persisting reviewed invoice."""

    document_id: UUID
    invoice_id: UUID | None
    document_type: str
    status: str
    booking_ids: list[str] = Field(default_factory=list)


class InvoiceListItem(BaseModel):
    """Invoice summary for search/list view."""

    id: UUID
    invoice_type: str
    invoice_number: str
    invoice_date: date
    party_name: str | None
    booking_references: list[str]
    total_amount: Decimal


class ListInvoicesResponse(BaseModel):
    """Response for invoice search endpoint."""

    invoices: list[InvoiceListItem]
    total: int


@router.get("", response_model=ListInvoicesResponse, status_code=200)
def list_invoices(
    invoice_number: Annotated[str | None, Query(description="Filter by invoice number")] = None,
    party: Annotated[str | None, Query(description="Filter by client/provider name")] = None,
    date_from: Annotated[date | None, Query(description="Date from (ISO)")] = None,
    date_to: Annotated[date | None, Query(description="Date to (ISO)")] = None,
    invoice_type: Annotated[
        InvoiceSearchType | None,
        Query(description="Filter by invoice type"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Maximum results")] = 100,
    use_case: ListInvoicesUseCase = Depends(get_list_invoices_use_case),
) -> ListInvoicesResponse:
    """Search persisted invoices by number, party, date range, and type."""
    try:
        items = use_case.execute(
            ListInvoicesRequest(
                invoice_number=invoice_number,
                party=party,
                date_from=date_from.isoformat() if date_from else None,
                date_to=date_to.isoformat() if date_to else None,
                invoice_type=invoice_type,
                limit=limit,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ListInvoicesResponse(
        invoices=[
            InvoiceListItem(
                id=item.id,
                invoice_type=item.invoice_type,
                invoice_number=item.invoice_number,
                invoice_date=item.invoice_date,
                party_name=item.party_name,
                booking_references=item.booking_references,
                total_amount=item.total_amount,
            )
            for item in items
        ],
        total=len(items),
    )


@router.post("/process", response_model=ProcessDocumentResponse, status_code=200)
def process_document(
    request: ProcessDocumentRequest,
    use_case: Annotated[ProcessInvoiceUseCase, Depends(get_process_invoice_use_case)],
) -> ProcessDocumentResponse:
    """Process a document with AI to extract invoice data.

    Returns extracted data for user preview/validation before saving.
    """
    try:
        dto_request = ProcessInvoiceRequest(document_id=request.document_id)
        result = use_case.execute(dto_request)

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

    except ValueError as e:
        error_msg = str(e)

        # Map specific errors to appropriate HTTP status codes
        if "not configured" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg) from e
        if "invalid" in error_msg.lower() and "key" in error_msg.lower():
            raise HTTPException(status_code=401, detail=error_msg) from e
        if "rate limit" in error_msg.lower():
            raise HTTPException(status_code=429, detail=error_msg) from e
        if "timed out" in error_msg.lower():
            raise HTTPException(status_code=504, detail=error_msg) from e

        raise HTTPException(status_code=400, detail=error_msg) from e


@router.post("/confirm", response_model=ConfirmDocumentResponse, status_code=200)
def confirm_document(
    request: ConfirmDocumentRequest,
    use_case: Annotated[ConfirmInvoiceUseCase, Depends(get_confirm_invoice_use_case)],
) -> ConfirmDocumentResponse:
    """Persist reviewed extraction data as invoice/booking/domain entities."""
    try:
        dto_request = ConfirmInvoiceRequest(
            document_id=request.document_id,
            document_type=request.document_type,
            ai_model=request.ai_model,
            raw_json=request.raw_json,
            overall_confidence=request.overall_confidence,
            manually_edited_fields=request.manually_edited_fields,
            invoice_number=request.invoice_number,
            invoice_date=(
                request.invoice_date.isoformat()
                if request.invoice_date is not None
                else None
            ),
            issuer_name=request.issuer_name,
            issuer_nif=request.issuer_nif,
            recipient_name=request.recipient_name,
            recipient_nif=request.recipient_nif,
            provider_type=(
                request.provider_type.value
                if request.provider_type is not None
                else None
            ),
            currency_valid=request.currency_valid,
            currency_detected=request.currency_detected,
            bl_references=request.bl_references,
            charges=[
                SaveChargeInput(
                    bl_reference=charge.bl_reference,
                    description=charge.description,
                    category=charge.category.value,
                    amount=str(charge.amount),
                    container=charge.container,
                )
                for charge in request.charges
            ],
            totals=request.totals,
            shipping_details=request.shipping_details,
        )

        result = use_case.execute(dto_request)
        return ConfirmDocumentResponse(
            document_id=result.document_id,
            invoice_id=result.invoice_id,
            document_type=result.document_type,
            status=result.status,
            booking_ids=result.booking_ids,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e
