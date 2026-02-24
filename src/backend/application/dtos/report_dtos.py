"""DTOs for reporting use cases."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CommissionReportRequest:
    """Request to generate a commission report."""

    date_from: str | None = None
    date_to: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class CommissionReportItem:
    """Single booking row in a commission report."""

    booking_id: str
    client_name: str | None
    created_at: datetime
    status: str
    total_revenue: Decimal
    total_costs: Decimal
    margin: Decimal
    commission: Decimal


@dataclass(frozen=True)
class CommissionReportTotals:
    """Aggregate totals for a commission report."""

    booking_count: int
    total_revenue: Decimal
    total_costs: Decimal
    total_margin: Decimal
    total_commission: Decimal


@dataclass(frozen=True)
class CommissionReportResponse:
    """Response payload for commission report generation."""

    items: list[CommissionReportItem] = field(default_factory=list)
    totals: CommissionReportTotals = field(
        default_factory=lambda: CommissionReportTotals(
            booking_count=0,
            total_revenue=Decimal("0.00"),
            total_costs=Decimal("0.00"),
            total_margin=Decimal("0.00"),
            total_commission=Decimal("0.00"),
        )
    )
