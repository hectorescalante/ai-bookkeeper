"""Integration tests for Document repository."""

from datetime import datetime, timedelta
from uuid import uuid4

from backend.adapters.persistence.repositories import SqlAlchemyDocumentRepository
from backend.domain.entities.document import Document
from backend.domain.enums import DocumentType, ErrorType, ProcessingStatus
from backend.domain.value_objects import EmailReference, ErrorInfo, FileHash


class TestDocumentRepository:
    """Test suite for SqlAlchemyDocumentRepository."""

    def test_save_and_retrieve_document(self, db_session):
        """Test saving and retrieving a document."""
        repo = SqlAlchemyDocumentRepository(db_session)

        # Create document
        file_hash = FileHash.sha256("abc123")
        email_ref = EmailReference(
            message_id="msg-123",
            subject="Invoice PDF",
            sender="sender@example.com",
            received_at=datetime.now(),
        )

        doc = Document.create(
            filename="invoice.pdf", file_hash=file_hash, email_reference=email_ref
        )

        repo.save(doc)

        # Retrieve
        retrieved = repo.find_by_id(doc.id)

        assert retrieved is not None
        assert retrieved.filename == "invoice.pdf"
        assert retrieved.file_hash.value == "abc123"
        assert retrieved.email_reference is not None
        assert retrieved.email_reference.message_id == "msg-123"

    def test_find_by_file_hash(self, db_session):
        """Test finding document by file hash (duplicate detection)."""
        repo = SqlAlchemyDocumentRepository(db_session)

        # Create and save
        file_hash = FileHash.sha256("duplicate_hash")
        doc = Document.create(filename="test.pdf", file_hash=file_hash)
        repo.save(doc)

        # Find by hash
        found = repo.find_by_file_hash(file_hash)

        assert found is not None
        assert found.id == doc.id

    def test_find_by_file_hash_not_found(self, db_session):
        """Test finding non-existent hash returns None."""
        repo = SqlAlchemyDocumentRepository(db_session)

        file_hash = FileHash.sha256("nonexistent")
        result = repo.find_by_file_hash(file_hash)

        assert result is None

    def test_list_by_status(self, db_session):
        """Test listing documents by status."""
        repo = SqlAlchemyDocumentRepository(db_session)

        # Create documents with different statuses
        doc1 = Document.create(filename="pending1.pdf", file_hash=FileHash.sha256("h1"))
        doc2 = Document.create(filename="pending2.pdf", file_hash=FileHash.sha256("h2"))
        doc3 = Document.create(filename="processed.pdf", file_hash=FileHash.sha256("h3"))

        doc3.mark_processed(DocumentType.CLIENT_INVOICE, uuid4())

        repo.save(doc1)
        repo.save(doc2)
        repo.save(doc3)

        # List pending
        pending = repo.list_by_status(ProcessingStatus.PENDING)

        assert len(pending) == 2
        assert all(d.status == ProcessingStatus.PENDING for d in pending)

        # List processed
        processed = repo.list_by_status(ProcessingStatus.PROCESSED)

        assert len(processed) == 1
        assert processed[0].status == ProcessingStatus.PROCESSED

    def test_find_stuck_processing(self, db_session):
        """Test finding documents stuck in PROCESSING status."""
        repo = SqlAlchemyDocumentRepository(db_session)

        # Create documents
        recent_doc = Document.create(filename="recent.pdf", file_hash=FileHash.sha256("r1"))
        recent_doc.start_processing()
        recent_doc.created_at = datetime.now() - timedelta(minutes=2)  # 2 min ago

        stuck_doc = Document.create(filename="stuck.pdf", file_hash=FileHash.sha256("s1"))
        stuck_doc.start_processing()
        stuck_doc.created_at = datetime.now() - timedelta(minutes=15)  # 15 min ago

        repo.save(recent_doc)
        repo.save(stuck_doc)

        # Find stuck (older than 10 minutes)
        stuck = repo.find_stuck_processing()

        assert len(stuck) == 1
        assert stuck[0].id == stuck_doc.id

    def test_update_document(self, db_session):
        """Test updating an existing document."""
        repo = SqlAlchemyDocumentRepository(db_session)

        # Create and save
        doc = Document.create(filename="test.pdf", file_hash=FileHash.sha256("h1"))
        repo.save(doc)

        # Update status
        doc.start_processing()
        repo.update(doc)

        # Retrieve and verify
        retrieved = repo.find_by_id(doc.id)
        assert retrieved is not None
        assert retrieved.status == ProcessingStatus.PROCESSING

        # Mark processed
        doc.mark_processed(DocumentType.PROVIDER_INVOICE, uuid4())
        repo.update(doc)

        # Verify again
        retrieved = repo.find_by_id(doc.id)
        assert retrieved is not None
        assert retrieved.status == ProcessingStatus.PROCESSED
        assert retrieved.document_type == DocumentType.PROVIDER_INVOICE

    def test_update_with_error_info(self, db_session):
        """Test updating document with error information."""
        repo = SqlAlchemyDocumentRepository(db_session)

        # Create document
        doc = Document.create(filename="error.pdf", file_hash=FileHash.sha256("e1"))
        repo.save(doc)

        # Add error
        error = ErrorInfo(
            error_type=ErrorType.AI_TIMEOUT,
            error_message="Request timed out after 60s",
            occurred_at=datetime.now(),
        )
        doc.mark_error(error)
        repo.update(doc)

        # Retrieve and verify
        retrieved = repo.find_by_id(doc.id)
        assert retrieved is not None
        assert retrieved.status == ProcessingStatus.ERROR
        assert retrieved.error_info is not None
        assert retrieved.error_info.error_type == ErrorType.AI_TIMEOUT
        assert retrieved.error_info.is_retryable is True
