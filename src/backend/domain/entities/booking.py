"""Booking entity - primary aggregate for commission calculation."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from backend.domain.enums import BookingStatus
from backend.domain.value_objects import BookingCharge, ClientInfo, Money, Port


@dataclass
class Booking:
    """Primary aggregate representing a shipping booking.

    A booking groups revenue (from client invoices) and costs (from provider invoices)
    to calculate the agent's commission.

    Commission formula: (Revenue - Costs) × commission_rate
    """

    id: str  # BL reference (editable)
    created_at: datetime
    client: ClientInfo | None = None
    pol: Port | None = None  # Port of Loading
    pod: Port | None = None  # Port of Discharge
    vessel: str | None = None
    containers: list[str] = field(default_factory=list)
    status: BookingStatus = BookingStatus.PENDING
    revenue_charges: list[BookingCharge] = field(default_factory=list)
    cost_charges: list[BookingCharge] = field(default_factory=list)
    _uuid: UUID = field(default_factory=uuid4)

    @classmethod
    def create(cls, bl_reference: str) -> "Booking":
        """Create a new booking with a BL reference."""
        return cls(
            id=bl_reference,
            created_at=datetime.now(),
        )

    @property
    def total_revenue(self) -> Money:
        """Calculate total revenue from all revenue charges."""
        if not self.revenue_charges:
            return Money.zero()
        return sum((c.amount for c in self.revenue_charges), Money.zero())

    @property
    def total_costs(self) -> Money:
        """Calculate total costs from all cost charges."""
        if not self.cost_charges:
            return Money.zero()
        return sum((c.amount for c in self.cost_charges), Money.zero())

    @property
    def margin(self) -> Money:
        """Calculate margin (revenue - costs).

        Note: Can be negative if costs exceed revenue.
        """
        return self.total_revenue - self.total_costs

    @property
    def margin_percentage(self) -> Decimal:
        """Calculate margin as percentage of revenue.

        Returns 0 if no revenue.
        """
        if self.total_revenue.is_zero():
            return Decimal("0.00")
        return (self.margin.amount / self.total_revenue.amount) * 100

    def calculate_agent_commission(self, rate: Decimal = Decimal("0.50")) -> Money:
        """Calculate agent commission.

        Args:
            rate: Commission rate (default 50%)

        Returns:
            Commission amount (can be negative if margin is negative)
        """
        return self.margin * rate

    def add_revenue_charge(self, charge: BookingCharge) -> None:
        """Add a revenue charge from a client invoice."""
        if charge.booking_id != self.id:
            raise ValueError(f"Charge booking_id {charge.booking_id} does not match {self.id}")
        self.revenue_charges.append(charge)

    def add_cost_charge(self, charge: BookingCharge) -> None:
        """Add a cost charge from a provider invoice."""
        if charge.booking_id != self.id:
            raise ValueError(f"Charge booking_id {charge.booking_id} does not match {self.id}")
        self.cost_charges.append(charge)

    def mark_complete(self) -> None:
        """Mark booking as complete."""
        self.status = BookingStatus.COMPLETE

    def revert_to_pending(self) -> None:
        """Revert booking to pending (if more invoices arrive)."""
        self.status = BookingStatus.PENDING

    @property
    def is_complete(self) -> bool:
        """Check if booking is complete."""
        return self.status == BookingStatus.COMPLETE

    @property
    def has_revenue(self) -> bool:
        """Check if booking has any revenue."""
        return len(self.revenue_charges) > 0

    @property
    def has_costs(self) -> bool:
        """Check if booking has any costs."""
        return len(self.cost_charges) > 0

    def update_client(self, client: ClientInfo) -> None:
        """Update client information."""
        self.client = client

    def update_ports(self, pol: Port | None = None, pod: Port | None = None) -> None:
        """Update port information."""
        if pol is not None:
            self.pol = pol
        if pod is not None:
            self.pod = pod

    def update_bl_reference(self, new_id: str) -> None:
        """Update BL reference (editable by user)."""
        self.id = new_id
