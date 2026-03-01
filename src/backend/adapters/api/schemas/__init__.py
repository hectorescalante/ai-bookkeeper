"""Pydantic schemas for API validation."""

from backend.adapters.api.schemas.booking_schemas import (
    BookingChargeItem,
    BookingDetailResponse,
    BookingListItem,
    ListBookingsParams,
    ListBookingsResponse,
)
from backend.adapters.api.schemas.config_schemas import (
    AgentRequest,
    AgentResponse,
    CompanyRequest,
    CompanyResponse,
    DiagnosticsExportResponse,
    SettingsRequest,
    SettingsResponse,
    TestGeminiConnectionRequest,
    TestGeminiConnectionResponse,
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
    SaveExportResponse,
)

__all__ = [
    # Config
    "AgentRequest",
    "AgentResponse",
    "CompanyRequest",
    "CompanyResponse",
    "DiagnosticsExportResponse",
    "SettingsRequest",
    "SettingsResponse",
    "TestGeminiConnectionRequest",
    "TestGeminiConnectionResponse",
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
    "SaveExportResponse",
    # Bookings
    "BookingChargeItem",
    "BookingListItem",
    "ListBookingsParams",
    "ListBookingsResponse",
    "BookingDetailResponse",
]
