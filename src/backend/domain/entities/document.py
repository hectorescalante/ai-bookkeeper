"""Document entity for PDF tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from backend.domain.enums import DocumentType, ProcessingStatus
from backend.domain.value_objects import EmailReference, ErrorInfo, FileHash


@dataclass
class Document:
    """A PDF document imported from email or manually.

    Tracks the processing status and links to the resulting invoice.
    """

    id: UUID
    filename: str
    file_hash: FileHash
    email_reference: EmailReference | None = None
    document_type: DocumentType | None = None  # Set after AI detection
    status: ProcessingStatus = ProcessingStatus.PENDING
    storage_path: str | None = None
    error_info: ErrorInfo | None = None
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: datetime | None = None
    invoice_id: UUID | None = None  # Link to resulting invoice

    @classmethod
    def create(
        cls,
        filename: str,
        file_hash: FileHash,
        email_reference: EmailReference | None = None,
        storage_path: str | None = None,
    ) -> "Document":
        """Create a new document."""
        return cls(
            id=uuid4(),
            filename=filename,
            file_hash=file_hash,
            email_reference=email_reference,
            storage_path=storage_path,
        )

    def start_processing(self, *, allow_reprocess: bool = False) -> None:
        """Mark document as being processed."""
        allowed_statuses = {ProcessingStatus.PENDING, ProcessingStatus.ERROR}
        if allow_reprocess:
            allowed_statuses.add(ProcessingStatus.PROCESSED)

        if self.status not in allowed_statuses:
            raise ValueError(f"Cannot start processing document in {self.status} status")
        self.status = ProcessingStatus.PROCESSING
        self.error_info = None

    def mark_processed(
        self,
        document_type: DocumentType,
        invoice_id: UUID | None = None,
    ) -> None:
        """Mark document as successfully processed."""
        self.status = ProcessingStatus.PROCESSED
        self.document_type = document_type
        self.invoice_id = invoice_id
        self.processed_at = datetime.now()
        self.error_info = None

    def mark_error(self, error_info: ErrorInfo) -> None:
        """Mark document as failed with error."""
        self.status = ProcessingStatus.ERROR
        self.error_info = error_info
        self.processed_at = datetime.now()

    def can_retry(self) -> bool:
        """Check if document can be retried."""
        if self.status != ProcessingStatus.ERROR:
            return False
        if self.error_info is None:
            return True
        return self.error_info.is_retryable

    @property
    def is_pending(self) -> bool:
        """Check if document is pending."""
        return self.status == ProcessingStatus.PENDING

    @property
    def is_processing(self) -> bool:
        """Check if document is being processed."""
        return self.status == ProcessingStatus.PROCESSING

    @property
    def is_processed(self) -> bool:
        """Check if document has been processed."""
        return self.status == ProcessingStatus.PROCESSED

    @property
    def is_error(self) -> bool:
        """Check if document has an error."""
        return self.status == ProcessingStatus.ERROR

    @property
    def is_invoice(self) -> bool:
        """Check if document is an invoice (client or provider)."""
        return self.document_type in (
            DocumentType.CLIENT_INVOICE,
            DocumentType.PROVIDER_INVOICE,
        )

    @property
    def is_other(self) -> bool:
        """Check if document is non-invoice (OTHER type)."""
        return self.document_type == DocumentType.OTHER
