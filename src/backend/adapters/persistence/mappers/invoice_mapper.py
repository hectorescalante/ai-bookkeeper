"""Mappers for invoice entities with JSON serialization."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.adapters.persistence.models.invoice import ClientInvoiceModel, ProviderInvoiceModel
from backend.domain.entities.invoice import ClientInvoice, ProviderInvoice
from backend.domain.enums import ChargeCategory, ConfidenceLevel, ProviderType
from backend.domain.value_objects import (
    BookingCharge,
    DocumentReference,
    ExtractionMetadata,
    FieldConfidence,
    FileHash,
    Money,
)

# --- JSON Serialization Helpers ---


def serialize_money(money: Money) -> dict[str, Any]:
    """Serialize Money to JSON dict."""
    return {"amount": str(money.amount), "currency": "EUR"}


def deserialize_money(data: dict[str, Any]) -> Money:
    """Deserialize Money from JSON dict."""
    return Money(amount=Decimal(data["amount"]))


def serialize_booking_charge(charge: BookingCharge) -> dict[str, Any]:
    """Serialize BookingCharge to JSON dict."""
    return {
        "booking_id": charge.booking_id,
        "invoice_id": str(charge.invoice_id),
        "charge_category": charge.charge_category.value,
        "provider_type": charge.provider_type.value if charge.provider_type else None,
        "container": charge.container,
        "description": charge.description,
        "amount": serialize_money(charge.amount),
    }


def deserialize_booking_charge(data: dict[str, Any]) -> BookingCharge:
    """Deserialize BookingCharge from JSON dict."""
    return BookingCharge(
        booking_id=data["booking_id"],
        invoice_id=UUID(data["invoice_id"]),
        charge_category=ChargeCategory(data["charge_category"]),
        provider_type=ProviderType(data["provider_type"]) if data.get("provider_type") else None,
        container=data.get("container"),
        description=data["description"],
        amount=deserialize_money(data["amount"]),
    )


def serialize_document_reference(doc_ref: DocumentReference | None) -> dict[str, Any] | None:
    """Serialize DocumentReference to JSON dict."""
    if not doc_ref:
        return None
    return {
        "document_id": str(doc_ref.document_id),
        "filename": doc_ref.filename,
        "file_hash": {"algorithm": doc_ref.file_hash.algorithm, "value": doc_ref.file_hash.value},
    }


def deserialize_document_reference(data: dict[str, Any] | None) -> DocumentReference | None:
    """Deserialize DocumentReference from JSON dict."""
    if not data:
        return None
    return DocumentReference(
        document_id=UUID(data["document_id"]),
        filename=data["filename"],
        file_hash=FileHash(
            algorithm=data["file_hash"]["algorithm"], value=data["file_hash"]["value"]
        ),
    )


def serialize_extraction_metadata(metadata: ExtractionMetadata | None) -> dict[str, Any] | None:
    """Serialize ExtractionMetadata to JSON dict."""
    if not metadata:
        return None
    return {
        "ai_model": metadata.ai_model,
        "overall_confidence": metadata.overall_confidence.value,
        "field_confidences": [
            {"field_name": fc.field_name, "confidence": fc.confidence.value}
            for fc in metadata.field_confidences
        ],
        "raw_json": metadata.raw_json,
        "manually_edited_fields": list(metadata.manually_edited_fields),
        "processed_at": metadata.processed_at.isoformat(),
    }


def deserialize_extraction_metadata(data: dict[str, Any] | None) -> ExtractionMetadata | None:
    """Deserialize ExtractionMetadata from JSON dict."""
    if not data:
        return None
    return ExtractionMetadata(
        ai_model=data["ai_model"],
        overall_confidence=ConfidenceLevel(data["overall_confidence"]),
        field_confidences=tuple(
            FieldConfidence(
                field_name=fc["field_name"], confidence=ConfidenceLevel(fc["confidence"])
            )
            for fc in data.get("field_confidences", [])
        ),
        raw_json=data.get("raw_json", ""),
        manually_edited_fields=tuple(data.get("manually_edited_fields", [])),
        processed_at=datetime.fromisoformat(data["processed_at"]),
    )


# --- ClientInvoice Mappers ---


def client_invoice_to_model(invoice: ClientInvoice) -> ClientInvoiceModel:
    """Convert ClientInvoice entity to ClientInvoiceModel ORM."""
    # Serialize charges to JSON
    charges_json = [serialize_booking_charge(charge) for charge in invoice.charges]

    # Serialize document reference (flatten to separate fields)
    doc_ref = invoice.source_document
    source_document_id = doc_ref.document_id if doc_ref else None
    source_document_filename = doc_ref.filename if doc_ref else None
    source_document_hash_algo = doc_ref.file_hash.algorithm if doc_ref else None
    source_document_hash_value = doc_ref.file_hash.value if doc_ref else None

    return ClientInvoiceModel(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        client_id=invoice.client_id,
        invoice_date=invoice.invoice_date,
        bl_reference=invoice.bl_reference,
        total_amount=invoice.total_amount.amount,
        total_currency="EUR",
        tax_amount=invoice.tax_amount.amount,
        tax_currency="EUR",
        charges=charges_json,
        source_document_id=source_document_id,
        source_document_filename=source_document_filename,
        source_document_hash_algo=source_document_hash_algo,
        source_document_hash_value=source_document_hash_value,
        extraction_metadata=serialize_extraction_metadata(invoice.extraction_metadata),
    )


def model_to_client_invoice(model: ClientInvoiceModel) -> ClientInvoice:
    """Convert ClientInvoiceModel ORM to ClientInvoice entity."""
    # Deserialize charges from JSON
    charges = [deserialize_booking_charge(charge_data) for charge_data in model.charges]

    # Reconstruct document reference
    source_document = None
    if model.source_document_id and model.source_document_hash_algo:
        source_document = DocumentReference(
            document_id=model.source_document_id,
            filename=model.source_document_filename or "",
            file_hash=FileHash(
                algorithm=model.source_document_hash_algo,
                value=model.source_document_hash_value or "",
            ),
        )

    return ClientInvoice(
        id=model.id,
        invoice_number=model.invoice_number,
        client_id=model.client_id,
        invoice_date=model.invoice_date,
        bl_reference=model.bl_reference,
        total_amount=Money(amount=model.total_amount),
        tax_amount=Money(amount=model.tax_amount),
        charges=charges,
        source_document=source_document,
        extraction_metadata=deserialize_extraction_metadata(model.extraction_metadata),
    )


# --- ProviderInvoice Mappers ---


def provider_invoice_to_model(invoice: ProviderInvoice) -> ProviderInvoiceModel:
    """Convert ProviderInvoice entity to ProviderInvoiceModel ORM."""
    # Serialize charges to JSON
    charges_json = [serialize_booking_charge(charge) for charge in invoice.charges]

    # Serialize document reference
    doc_ref = invoice.source_document
    source_document_id = doc_ref.document_id if doc_ref else None
    source_document_filename = doc_ref.filename if doc_ref else None
    source_document_hash_algo = doc_ref.file_hash.algorithm if doc_ref else None
    source_document_hash_value = doc_ref.file_hash.value if doc_ref else None

    return ProviderInvoiceModel(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        provider_id=invoice.provider_id,
        provider_type=invoice.provider_type.value,
        invoice_date=invoice.invoice_date,
        bl_references=invoice.bl_references,
        total_amount=invoice.total_amount.amount,
        total_currency="EUR",
        tax_amount=invoice.tax_amount.amount,
        tax_currency="EUR",
        charges=charges_json,
        source_document_id=source_document_id,
        source_document_filename=source_document_filename,
        source_document_hash_algo=source_document_hash_algo,
        source_document_hash_value=source_document_hash_value,
        extraction_metadata=serialize_extraction_metadata(invoice.extraction_metadata),
    )


def model_to_provider_invoice(model: ProviderInvoiceModel) -> ProviderInvoice:
    """Convert ProviderInvoiceModel ORM to ProviderInvoice entity."""
    # Deserialize charges from JSON
    charges = [deserialize_booking_charge(charge_data) for charge_data in model.charges]

    # Reconstruct document reference
    source_document = None
    if model.source_document_id and model.source_document_hash_algo:
        source_document = DocumentReference(
            document_id=model.source_document_id,
            filename=model.source_document_filename or "",
            file_hash=FileHash(
                algorithm=model.source_document_hash_algo,
                value=model.source_document_hash_value or "",
            ),
        )

    return ProviderInvoice(
        id=model.id,
        invoice_number=model.invoice_number,
        provider_id=model.provider_id,
        provider_type=ProviderType(model.provider_type),
        invoice_date=model.invoice_date,
        bl_references=model.bl_references,
        total_amount=Money(amount=model.total_amount),
        tax_amount=Money(amount=model.tax_amount),
        charges=charges,
        source_document=source_document,
        extraction_metadata=deserialize_extraction_metadata(model.extraction_metadata),
    )
