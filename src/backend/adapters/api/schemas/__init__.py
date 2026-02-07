"""Pydantic schemas for API validation."""

from backend.adapters.api.schemas.booking_schemas import (
    BookingDetailResponse,
    BookingListItem,
    ListBookingsParams,
    ListBookingsResponse,
)
from backend.adapters.api.schemas.config_schemas import (
    CompanyRequest,
    CompanyResponse,
    SettingsRequest,
    SettingsResponse,
)
from backend.adapters.api.schemas.document_schemas import (
    DocumentListItem,
    ListDocumentsParams,
    ListDocumentsResponse,
)

__all__ = [
    # Config
    "CompanyRequest",
    "CompanyResponse",
    "SettingsRequest",
    "SettingsResponse",
    # Documents
    "DocumentListItem",
    "ListDocumentsParams",
    "ListDocumentsResponse",
    # Bookings
    "BookingListItem",
    "ListBookingsParams",
    "ListBookingsResponse",
    "BookingDetailResponse",
]
