"""Use case for listing documents."""

from backend.application.dtos import DocumentListItem, ListDocumentsRequest
from backend.domain.enums import ProcessingStatus
from backend.ports.output.repositories import DocumentRepository


class ListDocumentsUseCase:
    """List documents with optional status filtering."""

    def __init__(self, document_repo: DocumentRepository):
        self.document_repo = document_repo

    def execute(self, request: ListDocumentsRequest) -> list[DocumentListItem]:
        """Execute the use case."""
        # Get documents by status, or all if no status specified
        if request.status:
            try:
                status = ProcessingStatus[request.status.upper()]
                documents = self.document_repo.list_by_status(status)
            except KeyError:
                raise ValueError(f"Invalid status: {request.status}") from None
        else:
            # Get all documents by fetching all statuses
            documents = []
            for status in ProcessingStatus:
                documents.extend(self.document_repo.list_by_status(status))

        # Sort by created_at descending (newest first)
        documents = sorted(documents, key=lambda d: d.created_at, reverse=True)

        # Apply limit
        documents = documents[: request.limit]

        # Convert to DTOs
        return [
            DocumentListItem(
                id=doc.id,
                filename=doc.filename,
                status=doc.status.value,
                document_type=doc.document_type.value if doc.document_type else None,
                created_at=doc.created_at,
                processed_at=doc.processed_at,
                email_sender=doc.email_reference.sender if doc.email_reference else None,
                email_subject=doc.email_reference.subject if doc.email_reference else None,
                error_message=doc.error_info.error_message if doc.error_info else None,
                error_retryable=doc.error_info.is_retryable if doc.error_info else None,
            )
            for doc in documents
        ]
