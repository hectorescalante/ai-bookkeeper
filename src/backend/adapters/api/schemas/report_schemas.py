"""Pydantic schemas for reports API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

BookingStatusFilter = Literal["PENDING", "COMPLETE"]
ReportInvoiceTypeFilter = Literal["CLIENT_INVOICE", "PROVIDER_INVOICE"]

class CommissionReportRequest(BaseModel):
    """Request body for commission report generation."""

    date_from: date | None = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: date | None = Field(None, description="End date (YYYY-MM-DD)")
    status: BookingStatusFilter | None = Field(None, description="Booking status filter")
    client: str | None = Field(None, description="Filter by client name")
    booking: str | None = Field(None, description="Filter by booking reference")
    invoice_type: ReportInvoiceTypeFilter | None = Field(
        None,
        description="Filter by invoice type (CLIENT_INVOICE or PROVIDER_INVOICE)",
    )


class CommissionReportItem(BaseModel):
    """Single booking row in a commission report."""

    booking_id: str
    client_name: str | None
    created_at: datetime
    status: str
    total_revenue: Decimal
    total_costs: Decimal
    margin: Decimal
    commission: Decimal


class CommissionReportTotals(BaseModel):
    """Aggregate report totals."""

    booking_count: int
    total_revenue: Decimal
    total_costs: Decimal
    total_margin: Decimal
    total_commission: Decimal


class CommissionReportResponse(BaseModel):
    """JSON response for commission report."""

    items: list[CommissionReportItem]
    totals: CommissionReportTotals


class ExportReportRequest(BaseModel):
    """Request body for report export."""

    date_from: date | None = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: date | None = Field(None, description="End date (YYYY-MM-DD)")
    status: BookingStatusFilter | None = Field(None, description="Booking status filter")
    client: str | None = Field(None, description="Filter by client name")
    booking: str | None = Field(None, description="Filter by booking reference")
    invoice_type: ReportInvoiceTypeFilter | None = Field(
        None,
        description="Filter by invoice type (CLIENT_INVOICE or PROVIDER_INVOICE)",
    )
    file_name: str | None = Field(None, description="Optional export filename")


class SaveExportResponse(BaseModel):
    """Response for reports saved to configured default path."""

    file_name: str
    saved_path: str
