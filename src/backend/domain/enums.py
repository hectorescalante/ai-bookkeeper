"""Domain enums for AI Bookkeeper."""

from enum import Enum


class BookingStatus(str, Enum):
    """Status of a booking."""

    PENDING = "PENDING"
    COMPLETE = "COMPLETE"


class ProcessingStatus(str, Enum):
    """Status of document processing."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    ERROR = "ERROR"


class DocumentType(str, Enum):
    """Type of document detected by AI."""

    CLIENT_INVOICE = "CLIENT_INVOICE"
    PROVIDER_INVOICE = "PROVIDER_INVOICE"
    OTHER = "OTHER"


class ProviderType(str, Enum):
    """Type of provider/vendor."""

    SHIPPING = "SHIPPING"
    CARRIER = "CARRIER"
    INSPECTION = "INSPECTION"
    OTHER = "OTHER"


class ChargeCategory(str, Enum):
    """Category of charge/service."""

    FREIGHT = "FREIGHT"
    HANDLING = "HANDLING"
    DOCUMENTATION = "DOCUMENTATION"
    TRANSPORT = "TRANSPORT"
    INSPECTION = "INSPECTION"
    INSURANCE = "INSURANCE"
    OTHER = "OTHER"


class ConfidenceLevel(str, Enum):
    """AI extraction confidence level."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @property
    def percentage(self) -> int:
        """Return percentage value for confidence level."""
        mapping = {
            ConfidenceLevel.HIGH: 100,
            ConfidenceLevel.MEDIUM: 70,
            ConfidenceLevel.LOW: 40,
        }
        return mapping[self]


class ErrorType(str, Enum):
    """Types of errors that can occur."""

    # Pre-condition errors
    NIF_NOT_CONFIGURED = "NIF_NOT_CONFIGURED"
    API_KEY_MISSING = "API_KEY_MISSING"
    API_KEY_INVALID = "API_KEY_INVALID"
    OUTLOOK_DISCONNECTED = "OUTLOOK_DISCONNECTED"

    # Runtime errors
    AI_TIMEOUT = "AI_TIMEOUT"
    AI_RATE_LIMIT = "AI_RATE_LIMIT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    TOO_MANY_PAGES = "TOO_MANY_PAGES"
    DISK_FULL = "DISK_FULL"
    ICLOUD_UNAVAILABLE = "ICLOUD_UNAVAILABLE"
    DUPLICATE_DOCUMENT = "DUPLICATE_DOCUMENT"
    INVALID_CURRENCY = "INVALID_CURRENCY"

    @property
    def is_retryable(self) -> bool:
        """Check if this error type is retryable."""
        retryable = {
            ErrorType.AI_TIMEOUT,
            ErrorType.AI_RATE_LIMIT,
            ErrorType.DISK_FULL,
            ErrorType.ICLOUD_UNAVAILABLE,
        }
        return self in retryable
