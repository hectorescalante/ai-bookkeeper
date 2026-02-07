"""Domain value objects - immutable data structures."""

from backend.domain.value_objects.charge import BookingCharge
from backend.domain.value_objects.document import (
    DocumentReference,
    EmailReference,
    FileHash,
)
from backend.domain.value_objects.error import ErrorInfo
from backend.domain.value_objects.extraction import ExtractionMetadata, FieldConfidence
from backend.domain.value_objects.identifiers import ClientInfo, Port
from backend.domain.value_objects.money import Money

__all__ = [
    "BookingCharge",
    "ClientInfo",
    "DocumentReference",
    "EmailReference",
    "ErrorInfo",
    "ExtractionMetadata",
    "FieldConfidence",
    "FileHash",
    "Money",
    "Port",
]
