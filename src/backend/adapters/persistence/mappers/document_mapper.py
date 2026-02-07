"""Mapper for Document entity."""

from backend.adapters.persistence.models.document import DocumentModel
from backend.domain.entities.document import Document
from backend.domain.enums import DocumentType, ErrorType, ProcessingStatus
from backend.domain.value_objects import EmailReference, ErrorInfo, FileHash


def document_to_model(document: Document) -> DocumentModel:
    """Convert Document entity to DocumentModel ORM."""
    # Extract email reference fields
    email_message_id = document.email_reference.message_id if document.email_reference else None
    email_subject = document.email_reference.subject if document.email_reference else None
    email_sender = document.email_reference.sender if document.email_reference else None
    email_received_at = document.email_reference.received_at if document.email_reference else None

    # Extract error info fields
    error_type = document.error_info.error_type.value if document.error_info else None
    error_message = document.error_info.error_message if document.error_info else None
    error_occurred_at = document.error_info.occurred_at if document.error_info else None
    error_retryable = document.error_info.is_retryable if document.error_info else None

    return DocumentModel(
        id=document.id,
        filename=document.filename,
        file_hash_algorithm=document.file_hash.algorithm,
        file_hash_value=document.file_hash.value,
        email_message_id=email_message_id,
        email_subject=email_subject,
        email_sender=email_sender,
        email_received_at=email_received_at,
        document_type=document.document_type.value if document.document_type else None,
        status=document.status.value,
        storage_path=document.storage_path,
        error_type=error_type,
        error_message=error_message,
        error_occurred_at=error_occurred_at,
        error_retryable=error_retryable,
        created_at=document.created_at,
        processed_at=document.processed_at,
        invoice_id=document.invoice_id,
    )


def model_to_document(model: DocumentModel) -> Document:
    """Convert DocumentModel ORM to Document entity."""
    # Reconstruct EmailReference if fields exist
    email_reference = None
    if model.email_message_id:
        email_reference = EmailReference(
            message_id=model.email_message_id,
            subject=model.email_subject or "",
            sender=model.email_sender or "",
            received_at=model.email_received_at,  # type: ignore
        )

    # Reconstruct ErrorInfo if fields exist
    error_info = None
    if model.error_type:
        error_info = ErrorInfo(
            error_type=ErrorType(model.error_type),
            error_message=model.error_message or "",
            occurred_at=model.error_occurred_at,  # type: ignore
        )

    return Document(
        id=model.id,
        filename=model.filename,
        file_hash=FileHash(algorithm=model.file_hash_algorithm, value=model.file_hash_value),
        email_reference=email_reference,
        document_type=DocumentType(model.document_type) if model.document_type else None,
        status=ProcessingStatus(model.status),
        storage_path=model.storage_path,
        error_info=error_info,
        created_at=model.created_at,
        processed_at=model.processed_at,
        invoice_id=model.invoice_id,
    )
