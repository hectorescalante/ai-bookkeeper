"""Pydantic schemas for reports API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

BookingStatusFilter = Literal["PENDING", "COMPLETE"]

class CommissionReportRequest(BaseModel):
    """Request body for commission report generation."""

    date_from: date | None = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: date | None = Field(None, description="End date (YYYY-MM-DD)")
    status: BookingStatusFilter | None = Field(None, description="Booking status filter")


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
    file_name: str | None = Field(None, description="Optional export filename")
