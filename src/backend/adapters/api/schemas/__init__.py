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
    FetchEmailsRequest,
    FetchEmailsResponse,
    ListDocumentsParams,
    ListDocumentsResponse,
)
from backend.adapters.api.schemas.report_schemas import (
    CommissionReportItem,
    CommissionReportRequest,
    CommissionReportResponse,
    CommissionReportTotals,
    ExportReportRequest,
)

__all__ = [
    # Config
    "CompanyRequest",
    "CompanyResponse",
    "SettingsRequest",
    "SettingsResponse",
    # Documents
    "DocumentListItem",
    "FetchEmailsRequest",
    "FetchEmailsResponse",
    "ListDocumentsParams",
    "ListDocumentsResponse",
    # Reports
    "CommissionReportItem",
    "CommissionReportRequest",
    "CommissionReportResponse",
    "CommissionReportTotals",
    "ExportReportRequest",
    # Bookings
    "BookingListItem",
    "ListBookingsParams",
    "ListBookingsResponse",
    "BookingDetailResponse",
]
