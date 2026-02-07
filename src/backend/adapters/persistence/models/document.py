"""SQLAlchemy model for Document entity."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.adapters.persistence.database import Base


class DocumentModel(Base):
    """ORM model for Document entity."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("file_hash_algorithm", "file_hash_value", name="uq_document_hash"),
        Index("ix_documents_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)

    # File hash for duplicate detection
    file_hash_algorithm: Mapped[str] = mapped_column(String(20), nullable=False)
    file_hash_value: Mapped[str] = mapped_column(String(128), nullable=False)

    # Email reference (nullable if uploaded manually)
    email_message_id: Mapped[str | None] = mapped_column(String(255))
    email_subject: Mapped[str | None] = mapped_column(String(500))
    email_sender: Mapped[str | None] = mapped_column(String(255))
    email_received_at: Mapped[datetime | None]

    # Document type (set after AI detection)
    document_type: Mapped[str | None] = mapped_column(
        String(20),
        CheckConstraint(
            "document_type IS NULL OR document_type IN "
            "('CLIENT_INVOICE', 'PROVIDER_INVOICE', 'OTHER')",
            name="ck_document_type",
        ),
    )

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'PROCESSED', 'ERROR')",
            name="ck_status",
        ),
        nullable=False,
        default="PENDING",
    )

    storage_path: Mapped[str | None] = mapped_column(String(1000))

    # Error information (nullable if no error)
    error_type: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)
    error_occurred_at: Mapped[datetime | None]
    error_retryable: Mapped[bool | None]

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    processed_at: Mapped[datetime | None]

    # Link to resulting invoice (nullable for OTHER documents)
    invoice_id: Mapped[UUID | None]
