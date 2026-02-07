"""Document-related value objects."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class FileHash:
    """Hash of a file for deduplication.

    Uses SHA-256 by default for reliable duplicate detection.
    """

    algorithm: str  # e.g., "sha256"
    value: str  # hex-encoded hash value

    @classmethod
    def sha256(cls, value: str) -> "FileHash":
        """Create a SHA-256 file hash."""
        return cls(algorithm="sha256", value=value)

    def __str__(self) -> str:
        """Format as string."""
        return f"{self.algorithm}:{self.value[:16]}..."


@dataclass(frozen=True, slots=True)
class EmailReference:
    """Reference to the source email.

    Stores metadata needed for deduplication and display.
    The email body is NOT stored.
    """

    message_id: str  # Unique email message ID
    subject: str
    sender: str  # Email address
    received_at: datetime


@dataclass(frozen=True, slots=True)
class DocumentReference:
    """Reference to a document (used in invoices)."""

    document_id: UUID
    filename: str
    file_hash: FileHash
