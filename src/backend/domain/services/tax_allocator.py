"""Tax allocation service for multi-booking invoices."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from backend.domain.value_objects import Money


@dataclass
class TaxAllocation:
    """Tax amount allocated to a specific booking."""

    bl_reference: str
    base_amount: Money  # Charges for this booking (before tax)
    tax_amount: Money  # Proportionally allocated tax
    percentage: Decimal  # Percentage of total


class TaxAllocator:
    """Service to distribute tax proportionally for multi-booking invoices.

    When a single provider invoice contains charges for multiple bookings,
    taxes must be distributed proportionally based on each booking's
    share of the total charges.

    Example:
        Invoice total: €1,000 (BL-001: €600, BL-002: €400, Tax: €210)
        - BL-001 receives: €600 charges + €126 tax (60%)
        - BL-002 receives: €400 charges + €84 tax (40%)
    """

    def allocate_tax(
        self,
        booking_amounts: dict[str, Money],
        total_tax: Money,
    ) -> list[TaxAllocation]:
        """Allocate tax proportionally across bookings.

        Args:
            booking_amounts: Dict of BL reference -> charge amount (before tax)
            total_tax: Total tax amount to distribute

        Returns:
            List of TaxAllocation for each booking

        Raises:
            ValueError: If no bookings provided or all amounts are zero
        """
        if not booking_amounts:
            raise ValueError("At least one booking amount is required")

        # Calculate total charges
        total_charges = sum(booking_amounts.values(), Money.zero())

        if total_charges.is_zero():
            raise ValueError("Total charges cannot be zero for tax allocation")

        allocations: list[TaxAllocation] = []
        allocated_tax = Money.zero()

        # Sort bookings for deterministic allocation
        sorted_bookings = sorted(booking_amounts.items(), key=lambda x: x[0])

        for i, (bl_reference, amount) in enumerate(sorted_bookings):
            # Calculate this booking's percentage
            percentage = (amount.amount / total_charges.amount * 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Calculate proportional tax
            if i == len(sorted_bookings) - 1:
                # Last booking gets remainder to avoid rounding issues
                tax_amount = total_tax - allocated_tax
            else:
                tax_amount = total_tax * (amount.amount / total_charges.amount)
                allocated_tax = allocated_tax + tax_amount

            allocations.append(
                TaxAllocation(
                    bl_reference=bl_reference,
                    base_amount=amount,
                    tax_amount=tax_amount,
                    percentage=percentage,
                )
            )

        return allocations

    def calculate_total_per_booking(
        self,
        allocations: list[TaxAllocation],
    ) -> dict[str, Money]:
        """Calculate total amount (charges + tax) per booking.

        Args:
            allocations: Tax allocations from allocate_tax

        Returns:
            Dict of BL reference -> total amount including tax
        """
        return {a.bl_reference: a.base_amount + a.tax_amount for a in allocations}
