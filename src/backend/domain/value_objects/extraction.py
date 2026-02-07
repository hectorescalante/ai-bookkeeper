"""AI extraction-related value objects."""

from dataclasses import dataclass, field
from datetime import datetime

from backend.domain.enums import ConfidenceLevel


@dataclass(frozen=True, slots=True)
class FieldConfidence:
    """Confidence level for a specific extracted field."""

    field_name: str
    confidence: ConfidenceLevel


@dataclass(frozen=True, slots=True)
class ExtractionMetadata:
    """Metadata about the AI extraction process.

    Stores information about how the data was extracted, including
    confidence levels and any manual edits made by the user.
    """

    ai_model: str  # e.g., "claude-sonnet-4-5-20250514"
    overall_confidence: ConfidenceLevel
    field_confidences: tuple[FieldConfidence, ...] = field(default_factory=tuple)
    raw_json: str = ""  # Original JSON response from AI
    manually_edited_fields: tuple[str, ...] = field(default_factory=tuple)
    processed_at: datetime = field(default_factory=datetime.now)

    def get_confidence_for(self, field_name: str) -> ConfidenceLevel | None:
        """Get confidence level for a specific field."""
        for fc in self.field_confidences:
            if fc.field_name == field_name:
                return fc.confidence
        return None

    def was_manually_edited(self, field_name: str) -> bool:
        """Check if a field was manually edited."""
        return field_name in self.manually_edited_fields

    @property
    def overall_confidence_percentage(self) -> int:
        """Get overall confidence as percentage."""
        return self.overall_confidence.percentage

    @classmethod
    def calculate_overall_confidence(
        cls,
        document_type_confidence: ConfidenceLevel,
        invoice_number_confidence: ConfidenceLevel,
        issuer_nif_confidence: ConfidenceLevel,
        recipient_nif_confidence: ConfidenceLevel,
        total_confidence: ConfidenceLevel,
    ) -> ConfidenceLevel:
        """Calculate overall confidence as minimum of critical fields.

        Per application.md: overall_confidence is the minimum confidence
        of critical fields.
        """
        confidences = [
            document_type_confidence,
            invoice_number_confidence,
            issuer_nif_confidence,
            recipient_nif_confidence,
            total_confidence,
        ]
        # Find minimum by percentage
        min_confidence = min(confidences, key=lambda c: c.percentage)
        return min_confidence
