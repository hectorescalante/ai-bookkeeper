"""DTOs for booking use cases."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class BookingListItem:
    """Booking summary for list view."""

    id: str  # BL reference
    client_name: str | None
    pol_code: str | None
    pod_code: str | None
    created_at: datetime
    status: str
    total_revenue: Decimal
    total_costs: Decimal
    margin: Decimal
    commission: Decimal
    document_count: int


@dataclass(frozen=True)
class BookingChargeItem:
    """Single charge line in booking detail response."""

    invoice_id: UUID
    charge_category: str
    provider_type: str | None
    container: str | None
    description: str
    amount: Decimal
    source_document_url: str | None = None


@dataclass(frozen=True)
class BookingDetailResponse:
    """Complete booking detail with charges."""

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
    cost_shipping: Decimal
    cost_carrier: Decimal
    cost_inspection: Decimal
    cost_other: Decimal
    margin: Decimal
    margin_percentage: Decimal
    commission_rate: Decimal
    agent_commission: Decimal
    commission: Decimal

    # Charges (simplified for API)
    revenue_charge_count: int
    cost_charge_count: int
    revenue_charges: list[BookingChargeItem] = field(default_factory=list)
    cost_charges: list[BookingChargeItem] = field(default_factory=list)


@dataclass(frozen=True)
class ListBookingsRequest:
    """Request to list bookings with filters."""

    client_id: UUID | None = None
    client: str | None = None
    status: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    sort_by: str = "created_at"
    descending: bool = True


@dataclass(frozen=True)
class EditBookingRequest:
    """Request to edit mutable booking fields."""

    bl_reference: str
    vessel: str | None = None
    containers: list[str] | None = None
    pol_code: str | None = None
    pol_name: str | None = None
    pod_code: str | None = None
    pod_name: str | None = None
