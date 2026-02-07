"""Invoice entities for revenue and cost tracking."""

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from backend.domain.enums import ProviderType
from backend.domain.value_objects import (
    BookingCharge,
    DocumentReference,
    ExtractionMetadata,
    Money,
)


@dataclass
class ClientInvoice:
    """Revenue invoice issued by the company to a client.

    The invoice_number is unique per issuer (per client).
    """

    id: UUID
    invoice_number: str
    client_id: UUID
    invoice_date: date
    bl_reference: str  # Primary booking this invoice belongs to
    total_amount: Money
    tax_amount: Money
    charges: list[BookingCharge] = field(default_factory=list)
    source_document: DocumentReference | None = None
    extraction_metadata: ExtractionMetadata | None = None

    @classmethod
    def create(
        cls,
        invoice_number: str,
        client_id: UUID,
        invoice_date: date,
        bl_reference: str,
        total_amount: Money,
        tax_amount: Money,
    ) -> "ClientInvoice":
        """Create a new client invoice."""
        return cls(
            id=uuid4(),
            invoice_number=invoice_number,
            client_id=client_id,
            invoice_date=invoice_date,
            bl_reference=bl_reference,
            total_amount=total_amount,
            tax_amount=tax_amount,
        )

    @property
    def net_amount(self) -> Money:
        """Calculate net amount (total - tax)."""
        return self.total_amount - self.tax_amount

    def add_charge(self, charge: BookingCharge) -> None:
        """Add a charge to this invoice."""
        self.charges.append(charge)


@dataclass
class ProviderInvoice:
    """Cost invoice received from a provider.

    The invoice_number is unique per issuer (per provider).
    A provider invoice may contain charges for multiple bookings.
    """

    id: UUID
    invoice_number: str
    provider_id: UUID
    provider_type: ProviderType
    invoice_date: date
    bl_references: list[str]  # Can have multiple BL references
    total_amount: Money
    tax_amount: Money
    charges: list[BookingCharge] = field(default_factory=list)
    source_document: DocumentReference | None = None
    extraction_metadata: ExtractionMetadata | None = None

    @classmethod
    def create(
        cls,
        invoice_number: str,
        provider_id: UUID,
        provider_type: ProviderType,
        invoice_date: date,
        bl_references: list[str],
        total_amount: Money,
        tax_amount: Money,
    ) -> "ProviderInvoice":
        """Create a new provider invoice."""
        return cls(
            id=uuid4(),
            invoice_number=invoice_number,
            provider_id=provider_id,
            provider_type=provider_type,
            invoice_date=invoice_date,
            bl_references=bl_references,
            total_amount=total_amount,
            tax_amount=tax_amount,
        )

    @property
    def net_amount(self) -> Money:
        """Calculate net amount (total - tax)."""
        return self.total_amount - self.tax_amount

    @property
    def is_multi_booking(self) -> bool:
        """Check if invoice has charges for multiple bookings."""
        return len(self.bl_references) > 1

    def add_charge(self, charge: BookingCharge) -> None:
        """Add a charge to this invoice."""
        self.charges.append(charge)

    def get_charges_for_booking(self, bl_reference: str) -> list[BookingCharge]:
        """Get charges attributed to a specific booking."""
        return [c for c in self.charges if c.booking_id == bl_reference]

    def get_total_for_booking(self, bl_reference: str) -> Money:
        """Get total amount for a specific booking."""
        charges = self.get_charges_for_booking(bl_reference)
        if not charges:
            return Money.zero()
        return sum((c.amount for c in charges), Money.zero())
