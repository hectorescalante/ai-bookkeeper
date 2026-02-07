"""Charge-related value objects."""

from dataclasses import dataclass
from uuid import UUID

from backend.domain.enums import ChargeCategory, ProviderType
from backend.domain.value_objects.money import Money


@dataclass(frozen=True, slots=True)
class BookingCharge:
    """A charge attributed to a booking from an invoice.

    Charges are extracted from invoices and attributed to specific bookings.
    The charge_category describes the service type, while provider_type
    identifies who provided it.
    """

    booking_id: str  # BL reference
    invoice_id: UUID
    charge_category: ChargeCategory
    provider_type: ProviderType | None  # None for client invoices (revenue)
    container: str | None  # Container number if applicable
    description: str
    amount: Money

    def is_cost(self) -> bool:
        """Check if this is a cost (from provider invoice)."""
        return self.provider_type is not None

    def is_revenue(self) -> bool:
        """Check if this is revenue (from client invoice)."""
        return self.provider_type is None
