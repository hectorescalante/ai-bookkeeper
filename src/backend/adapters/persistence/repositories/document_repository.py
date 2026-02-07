"""SQLite repository for Document entity."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from backend.adapters.persistence.mappers import document_to_model, model_to_document
from backend.adapters.persistence.models.document import DocumentModel
from backend.domain.entities.document import Document
from backend.domain.enums import ProcessingStatus
from backend.domain.value_objects import FileHash
from backend.ports.output.repositories import DocumentRepository


class SqlAlchemyDocumentRepository(DocumentRepository):
    """SQLite implementation of DocumentRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, document: Document) -> None:
        """Save a new document."""
        model = document_to_model(document)
        self.session.add(model)
        self.session.commit()

    def find_by_id(self, document_id: UUID) -> Document | None:
        """Find document by ID."""
        model = self.session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if model is None:
            return None
        return model_to_document(model)

    def find_by_file_hash(self, file_hash: FileHash) -> Document | None:
        """Find document by file hash (for duplicate detection)."""
        model = (
            self.session.query(DocumentModel)
            .filter(
                DocumentModel.file_hash_algorithm == file_hash.algorithm,
                DocumentModel.file_hash_value == file_hash.value,
            )
            .first()
        )
        if model is None:
            return None
        return model_to_document(model)

    def list_by_status(self, status: ProcessingStatus) -> list[Document]:
        """List documents by processing status."""
        models = (
            self.session.query(DocumentModel)
            .filter(DocumentModel.status == status.value)
            .order_by(DocumentModel.created_at.desc())
            .all()
        )
        return [model_to_document(model) for model in models]

    def find_stuck_processing(self) -> list[Document]:
        """Find documents stuck in PROCESSING status (crash recovery).

        Documents that have been in PROCESSING status for more than 10 minutes
        are considered stuck (likely due to app crash or network timeout).
        """
        threshold = datetime.now() - timedelta(minutes=10)

        models = (
            self.session.query(DocumentModel)
            .filter(
                DocumentModel.status == ProcessingStatus.PROCESSING.value,
                DocumentModel.created_at < threshold,
            )
            .order_by(DocumentModel.created_at)
            .all()
        )
        return [model_to_document(model) for model in models]

    def update(self, document: Document) -> None:
        """Update an existing document."""
        model = self.session.query(DocumentModel).filter(DocumentModel.id == document.id).first()

        if model is None:
            raise ValueError(f"Document {document.id} not found")

        # Update model fields from entity
        updated_model = document_to_model(document)

        model.filename = updated_model.filename
        model.document_type = updated_model.document_type
        model.status = updated_model.status
        model.storage_path = updated_model.storage_path
        model.error_type = updated_model.error_type
        model.error_message = updated_model.error_message
        model.error_occurred_at = updated_model.error_occurred_at
        model.error_retryable = updated_model.error_retryable
        model.processed_at = updated_model.processed_at
        model.invoice_id = updated_model.invoice_id

        self.session.commit()
