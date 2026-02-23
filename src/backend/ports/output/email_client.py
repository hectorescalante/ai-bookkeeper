"""Output port: Email client interface for mailbox document intake."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EmailAttachment:
    """Attachment found in an email message."""

    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True, slots=True)
class EmailMessage:
    """Email message data relevant for document ingestion."""

    message_id: str
    subject: str
    sender: str
    received_at: datetime
    attachments: tuple[EmailAttachment, ...] = field(default_factory=tuple)


class EmailClient(ABC):
    """Abstract email client interface for fetching PDF attachments."""

    @abstractmethod
    def fetch_messages_with_pdf_attachments(
        self, max_messages: int = 25
    ) -> list[EmailMessage]:
        """Fetch unread messages that include PDF attachments."""
        pass


class EmailClientError(Exception):
    """Base exception for email client failures."""

    pass


class EmailAuthError(EmailClientError):
    """Raised when email authentication is invalid or expired."""

    pass


class EmailRateLimitError(EmailClientError):
    """Raised when mailbox API rate limits are hit."""

    def __init__(self, retry_after_seconds: int | None = None) -> None:
        self.retry_after_seconds = retry_after_seconds
        detail = (
            f"Retry after {retry_after_seconds} seconds."
            if retry_after_seconds is not None
            else "Retry later."
        )
        super().__init__(f"Mailbox API rate limited. {detail}")
