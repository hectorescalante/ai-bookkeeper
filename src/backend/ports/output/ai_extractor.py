"""Output port: AI Extractor interface for invoice data extraction.

Defines the contract for AI-powered invoice data extraction,
following the dependency inversion principle.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractionResult:
    """Result of AI invoice extraction.

    Contains the structured data extracted from a PDF invoice,
    including confidence levels for each field.
    """

    raw_json: str  # Original JSON string from AI
    parsed_data: dict[str, Any]  # Parsed JSON response
    model_used: str  # e.g., "gemini-3-pro"

    @property
    def document_type(self) -> str | None:
        """Get the detected document type."""
        return self.parsed_data.get("document_type")

    @property
    def document_type_confidence(self) -> str | None:
        """Get document type confidence."""
        return self.parsed_data.get("document_type_confidence")

    @property
    def invoice_data(self) -> dict[str, Any] | None:
        """Get the invoice data section."""
        return self.parsed_data.get("invoice")

    @property
    def extraction_notes(self) -> str | None:
        """Get any extraction notes from the AI."""
        return self.parsed_data.get("extraction_notes")


@dataclass
class PDFContent:
    """Content extracted from a PDF for AI processing.

    Can contain text content, image data (for scanned pages), or both.
    """

    text_content: str = ""
    page_images: list[bytes] = field(default_factory=list)  # PNG image bytes per page
    page_count: int = 0
    is_scanned: bool = False
    filename: str = ""

    @property
    def has_text(self) -> bool:
        """Check if text content is available."""
        return bool(self.text_content.strip())

    @property
    def has_images(self) -> bool:
        """Check if page images are available."""
        return bool(self.page_images)


class AIExtractor(ABC):
    """Abstract interface for AI-powered invoice data extraction.

    Implementations should handle sending PDF content to an AI model
    and parsing the structured response.
    """

    @abstractmethod
    def extract_invoice_data(
        self,
        pdf_content: PDFContent,
        company_nif: str,
        extraction_prompt: str,
    ) -> ExtractionResult:
        """Extract structured invoice data from PDF content.

        Args:
            pdf_content: The PDF content (text and/or images)
            company_nif: Company NIF for invoice classification
            extraction_prompt: The prompt template to use

        Returns:
            ExtractionResult with parsed data

        Raises:
            AITimeoutError: If the AI request times out
            AIRateLimitError: If rate limited
            AIAuthError: If API key is invalid
            AIExtractionError: For other AI errors
        """
        pass

    @abstractmethod
    def test_connection(self, api_key: str) -> bool:
        """Test that the API key is valid.

        Args:
            api_key: The API key to test

        Returns:
            True if the connection is successful
        """
        pass


# --- Custom Exceptions ---


class AIExtractionError(Exception):
    """Base exception for AI extraction errors."""

    pass


class AITimeoutError(AIExtractionError):
    """Raised when AI request times out."""

    pass


class AIRateLimitError(AIExtractionError):
    """Raised when rate limited by AI provider."""

    def __init__(self, retry_after_minutes: int = 0):
        self.retry_after_minutes = retry_after_minutes
        super().__init__(f"Rate limited. Retry after {retry_after_minutes} minutes.")


class AIAuthError(AIExtractionError):
    """Raised when API key is invalid."""

    pass
