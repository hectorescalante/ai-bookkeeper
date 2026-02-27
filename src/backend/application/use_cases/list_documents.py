"""Use case for listing documents."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from backend.application.dtos import DocumentListItem, ListDocumentsRequest
from backend.domain.entities.document import Document
from backend.domain.enums import DocumentType, ProcessingStatus
from backend.ports.output.repositories import (
    ClientRepository,
    DocumentRepository,
    InvoiceRepository,
    ProviderRepository,
)


class ListDocumentsUseCase:
    """List documents with optional status filtering."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        invoice_repo: InvoiceRepository,
        client_repo: ClientRepository,
        provider_repo: ProviderRepository,
    ) -> None:
        self.document_repo = document_repo
        self.invoice_repo = invoice_repo
        self.client_repo = client_repo
        self.provider_repo = provider_repo

    def execute(self, request: ListDocumentsRequest) -> list[DocumentListItem]:
        """Execute the use case."""
        date_from = self._parse_date(request.date_from, field_name="date_from")
        date_to = self._parse_date(request.date_to, field_name="date_to")
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from cannot be greater than date_to")

        requested_document_type: DocumentType | None = None
        if request.document_type:
            try:
                requested_document_type = DocumentType(request.document_type.upper())
            except ValueError as exc:
                raise ValueError(f"Invalid document_type: {request.document_type}") from exc

        party_filter = (request.party or "").strip().lower()
        booking_filter = (request.booking or "").strip().lower()

        documents = self._get_documents(request.status)
        documents = sorted(documents, key=lambda doc: doc.created_at, reverse=True)
        email_pdf_counts = self._build_email_pdf_counts(documents)

        items: list[DocumentListItem] = []
        for doc in documents:
            if requested_document_type and doc.document_type != requested_document_type:
                continue

            filter_date = (doc.processed_at or doc.created_at).date()
            if date_from and filter_date < date_from:
                continue
            if date_to and filter_date > date_to:
                continue

            (
                invoice_number,
                party_name,
                booking_references,
                total_amount,
                manually_edited_fields,
            ) = self._get_metadata(doc)

            if party_filter and party_filter not in (party_name or "").lower():
                continue
            if booking_filter and not any(
                booking_filter in reference.lower() for reference in booking_references
            ):
                continue

            items.append(
                DocumentListItem(
                    id=doc.id,
                    filename=doc.filename,
                    status=doc.status.value,
                    document_type=doc.document_type.value if doc.document_type else None,
                    created_at=doc.created_at,
                    processed_at=doc.processed_at,
                    email_sender=doc.email_reference.sender if doc.email_reference else None,
                    email_subject=doc.email_reference.subject if doc.email_reference else None,
                    pdf_count_in_email=(
                        email_pdf_counts.get(doc.email_reference.message_id, 1)
                        if doc.email_reference is not None
                        else None
                    ),
                    error_message=doc.error_info.error_message if doc.error_info else None,
                    error_retryable=doc.error_info.is_retryable if doc.error_info else None,
                    invoice_number=invoice_number,
                    party_name=party_name,
                    booking_references=booking_references,
                    total_amount=total_amount,
                    file_url=f"/api/documents/{doc.id}/file" if doc.storage_path else None,
                    manually_edited_fields=manually_edited_fields,
                )
            )

            if len(items) >= request.limit:
                break

        return items

    def _get_documents(self, status: str | None) -> list[Document]:
        if status:
            try:
                target_status = ProcessingStatus[status.upper()]
            except KeyError:
                raise ValueError(f"Invalid status: {status}") from None
            return self.document_repo.list_by_status(target_status)

        documents = []
        for current_status in ProcessingStatus:
            documents.extend(self.document_repo.list_by_status(current_status))
        return documents

    @staticmethod
    def _build_email_pdf_counts(documents: list[Document]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for document in documents:
            email_reference = document.email_reference
            if email_reference is None:
                continue
            counts[email_reference.message_id] = (
                counts.get(email_reference.message_id, 0) + 1
            )
        return counts

    def _get_metadata(
        self,
        document: Document,
    ) -> tuple[str | None, str | None, list[str], Decimal | None, list[str]]:
        if document.invoice_id is None:
            return None, None, [], None, []

        invoice_id: UUID = document.invoice_id
        if document.document_type == DocumentType.CLIENT_INVOICE:
            client_invoice = self.invoice_repo.find_client_invoice_by_id(invoice_id)
            if client_invoice is None:
                return None, None, [], None, []
            client = self.client_repo.find_by_id(client_invoice.client_id)
            party_name = client.name if client is not None else None
            manually_edited_fields = list(
                client_invoice.extraction_metadata.manually_edited_fields
            ) if client_invoice.extraction_metadata is not None else []
            return (
                client_invoice.invoice_number,
                party_name,
                [client_invoice.bl_reference],
                client_invoice.total_amount.amount,
                manually_edited_fields,
            )

        if document.document_type == DocumentType.PROVIDER_INVOICE:
            provider_invoice = self.invoice_repo.find_provider_invoice_by_id(invoice_id)
            if provider_invoice is None:
                return None, None, [], None, []
            provider = self.provider_repo.find_by_id(provider_invoice.provider_id)
            party_name = provider.name if provider is not None else None
            manually_edited_fields = list(
                provider_invoice.extraction_metadata.manually_edited_fields
            ) if provider_invoice.extraction_metadata is not None else []
            return (
                provider_invoice.invoice_number,
                party_name,
                list(provider_invoice.bl_references),
                provider_invoice.total_amount.amount,
                manually_edited_fields,
            )

        return None, None, [], None, []

    @staticmethod
    def _parse_date(value: str | None, field_name: str) -> date | None:
        if value is None or not value.strip():
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Invalid {field_name}: {value}") from exc
