"""Pydantic schemas for booking API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class BookingListItem(BaseModel):
    """Booking summary for list view."""

    id: str  # BL reference
    client_name: str | None
    created_at: datetime
    status: str
    total_revenue: Decimal
    total_costs: Decimal
    margin: Decimal
    commission: Decimal
    document_count: int


class ListBookingsResponse(BaseModel):
    """Response for list bookings endpoint."""

    bookings: list[BookingListItem]
    total: int


class ListBookingsParams(BaseModel):
    """Query parameters for list bookings endpoint."""

    client_id: UUID | None = Field(None, description="Filter by client ID")
    status: str | None = Field(None, description="Filter by status (PENDING, COMPLETE)")
    date_from: str | None = Field(None, description="Filter by date from (ISO format)")
    date_to: str | None = Field(None, description="Filter by date to (ISO format)")
    sort_by: str = Field("created_at", description="Sort field (created_at, margin, commission)")
    descending: bool = Field(True, description="Sort in descending order")


class BookingChargeItem(BaseModel):
    """Single charge line in booking detail."""

    invoice_id: UUID
    charge_category: str
    provider_type: str | None
    container: str | None
    description: str
    amount: Decimal


class BookingDetailResponse(BaseModel):
    """Complete booking detail response."""

    id: str  # BL reference
    created_at: datetime
    status: str

    # Client info
    client_id: UUID | None
    client_name: str | None
    client_nif: str | None

    # Shipping info
    pol_code: str | None
    pol_name: str | None
    pod_code: str | None
    pod_name: str | None
    vessel: str | None
    containers: list[str]

    # Financial summary
    total_revenue: Decimal
    total_costs: Decimal
    margin: Decimal
    margin_percentage: Decimal
    commission: Decimal

    # Charges
    revenue_charge_count: int
    cost_charge_count: int
    revenue_charges: list[BookingChargeItem]
    cost_charges: list[BookingChargeItem]
