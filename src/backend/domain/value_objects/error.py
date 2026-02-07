"""Error-related value objects."""

from dataclasses import dataclass, field
from datetime import datetime

from backend.domain.enums import ErrorType


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """Information about an error that occurred.

    Used to track errors on documents and provide user-friendly messages.
    """

    error_type: ErrorType
    error_message: str
    occurred_at: datetime = field(default_factory=datetime.now)

    @property
    def is_retryable(self) -> bool:
        """Check if this error can be retried."""
        return self.error_type.is_retryable

    @classmethod
    def nif_not_configured(cls) -> "ErrorInfo":
        """Create NIF not configured error."""
        return cls(
            error_type=ErrorType.NIF_NOT_CONFIGURED,
            error_message="Configure company NIF in Settings before processing invoices.",
        )

    @classmethod
    def api_key_missing(cls) -> "ErrorInfo":
        """Create API key missing error."""
        return cls(
            error_type=ErrorType.API_KEY_MISSING,
            error_message="Configure API key in Settings.",
        )

    @classmethod
    def api_key_invalid(cls) -> "ErrorInfo":
        """Create API key invalid error."""
        return cls(
            error_type=ErrorType.API_KEY_INVALID,
            error_message="API key is invalid. Please check your Anthropic API key in Settings.",
        )

    @classmethod
    def ai_timeout(cls) -> "ErrorInfo":
        """Create AI timeout error."""
        return cls(
            error_type=ErrorType.AI_TIMEOUT,
            error_message="AI processing timed out. Please try again.",
        )

    @classmethod
    def ai_rate_limit(cls, retry_after_minutes: int = 5) -> "ErrorInfo":
        """Create AI rate limit error."""
        return cls(
            error_type=ErrorType.AI_RATE_LIMIT,
            error_message=f"Rate limit reached. Try again in {retry_after_minutes} minutes.",
        )

    @classmethod
    def file_too_large(cls, size_mb: float, max_mb: int = 20) -> "ErrorInfo":
        """Create file too large error."""
        return cls(
            error_type=ErrorType.FILE_TOO_LARGE,
            error_message=f"File size ({size_mb:.1f}MB) exceeds limit ({max_mb}MB).",
        )

    @classmethod
    def too_many_pages(cls, pages: int, max_pages: int = 50) -> "ErrorInfo":
        """Create too many pages error."""
        return cls(
            error_type=ErrorType.TOO_MANY_PAGES,
            error_message=f"PDF has {pages} pages, maximum is {max_pages}.",
        )

    @classmethod
    def duplicate_document(cls) -> "ErrorInfo":
        """Create duplicate document error."""
        return cls(
            error_type=ErrorType.DUPLICATE_DOCUMENT,
            error_message="Document already imported.",
        )

    @classmethod
    def invalid_currency(cls, detected_currency: str) -> "ErrorInfo":
        """Create invalid currency error."""
        return cls(
            error_type=ErrorType.INVALID_CURRENCY,
            error_message=f"Invoice currency is {detected_currency}. Only EUR invoices are supported.",
        )
