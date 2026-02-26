"""DTOs for invoice processing use cases."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ProcessInvoiceRequest:
    """Request to process a document with AI extraction."""

    document_id: UUID
    allow_processed: bool = False


@dataclass(frozen=True)
class ProcessInvoiceResponse:
    """Response from AI invoice extraction (preview for user validation).

    Contains the extracted data for user review before saving.
    """

    document_id: UUID
    document_type: str  # CLIENT_INVOICE, PROVIDER_INVOICE, OTHER
    document_type_confidence: str
    ai_model: str
    raw_json: str

    # Extracted invoice fields (for user preview)
    invoice_number: str | None = None
    invoice_date: str | None = None
    issuer_name: str | None = None
    issuer_nif: str | None = None
    recipient_name: str | None = None
    recipient_nif: str | None = None
    provider_type: str | None = None
    currency_valid: bool = True
    currency_detected: str = "EUR"

    bl_references: list[dict[str, Any]] = field(default_factory=list)
    charges: list[dict[str, Any]] = field(default_factory=list)
    totals: dict[str, Any] = field(default_factory=dict)

    extraction_notes: str | None = None

    # Validation
    overall_confidence: str = "HIGH"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SaveChargeInput:
    """Single reviewed charge line to persist."""

    bl_reference: str | None
    description: str
    category: str
    amount: str
    container: str | None = None


@dataclass(frozen=True)
class ConfirmInvoiceRequest:
    """Request to confirm reviewed extraction data and persist invoice entities."""

    document_id: UUID
    document_type: str
    ai_model: str
    raw_json: str
    overall_confidence: str = "HIGH"
    manually_edited_fields: list[str] = field(default_factory=list)

    invoice_number: str | None = None
    invoice_date: str | None = None
    issuer_name: str | None = None
    issuer_nif: str | None = None
    recipient_name: str | None = None
    recipient_nif: str | None = None
    provider_type: str | None = None
    currency_valid: bool = True
    currency_detected: str = "EUR"

    bl_references: list[str | dict[str, Any]] = field(default_factory=list)
    charges: list[SaveChargeInput] = field(default_factory=list)
    totals: dict[str, Any] = field(default_factory=dict)
    shipping_details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConfirmInvoiceResponse:
    """Response after persisting a reviewed invoice."""

    document_id: UUID
    invoice_id: UUID | None
    document_type: str
    status: str
    booking_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ListInvoicesRequest:
    """Request to list/search persisted invoices."""

    invoice_number: str | None = None
    party: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    invoice_type: str | None = None
    limit: int = 100


@dataclass(frozen=True)
class InvoiceListItem:
    """Unified invoice row for search results."""

    id: UUID
    invoice_type: str
    invoice_number: str
    invoice_date: date
    party_name: str | None
    booking_references: list[str]
    total_amount: Decimal
