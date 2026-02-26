"""Use case for viewing booking details."""

from decimal import Decimal
from uuid import UUID

from backend.application.dtos import BookingChargeItem, BookingDetailResponse
from backend.domain.enums import ProviderType
from backend.domain.value_objects import BookingCharge
from backend.ports.output.repositories import BookingRepository, InvoiceRepository


class ViewBookingDetailUseCase:
    """View complete booking details."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        invoice_repo: InvoiceRepository,
        company_commission_rate: Decimal = Decimal("0.50"),
    ):
        self.booking_repo = booking_repo
        self.invoice_repo = invoice_repo
        self.commission_rate = company_commission_rate

    def execute(self, bl_reference: str) -> BookingDetailResponse | None:
        """Execute the use case."""
        booking = self.booking_repo.find_by_id(bl_reference)

        if not booking:
            return None

        commission_amount = booking.calculate_agent_commission(self.commission_rate).amount
        source_document_urls: dict[UUID, str | None] = {}
        cost_totals = self._cost_totals_by_provider_type(booking.cost_charges)

        return BookingDetailResponse(
            id=booking.id,
            created_at=booking.created_at,
            status=booking.status.value,
            client_id=booking.client.client_id if booking.client else None,
            client_name=booking.client.name if booking.client else None,
            client_nif=booking.client.nif if booking.client else None,
            pol_code=booking.pol.code if booking.pol else None,
            pol_name=booking.pol.name if booking.pol else None,
            pod_code=booking.pod.code if booking.pod else None,
            pod_name=booking.pod.name if booking.pod else None,
            vessel=booking.vessel,
            containers=booking.containers,
            total_revenue=booking.total_revenue.amount,
            total_costs=booking.total_costs.amount,
            cost_shipping=cost_totals[ProviderType.SHIPPING],
            cost_carrier=cost_totals[ProviderType.CARRIER],
            cost_inspection=cost_totals[ProviderType.INSPECTION],
            cost_other=cost_totals[ProviderType.OTHER],
            margin=booking.margin.amount,
            margin_percentage=booking.margin_percentage,
            commission_rate=self.commission_rate,
            agent_commission=commission_amount,
            commission=commission_amount,
            revenue_charge_count=len(booking.revenue_charges),
            cost_charge_count=len(booking.cost_charges),
            revenue_charges=[
                BookingChargeItem(
                    invoice_id=charge.invoice_id,
                    charge_category=charge.charge_category.value,
                    provider_type=(
                        charge.provider_type.value if charge.provider_type is not None else None
                    ),
                    container=charge.container,
                    description=charge.description,
                    amount=charge.amount.amount,
                    source_document_url=self._source_document_url(
                        charge.invoice_id, source_document_urls
                    ),
                )
                for charge in booking.revenue_charges
            ],
            cost_charges=[
                BookingChargeItem(
                    invoice_id=charge.invoice_id,
                    charge_category=charge.charge_category.value,
                    provider_type=(
                        charge.provider_type.value if charge.provider_type is not None else None
                    ),
                    container=charge.container,
                    description=charge.description,
                    amount=charge.amount.amount,
                    source_document_url=self._source_document_url(
                        charge.invoice_id, source_document_urls
                    ),
                )
                for charge in booking.cost_charges
            ],
        )

    def _cost_totals_by_provider_type(
        self, charges: list[BookingCharge]
    ) -> dict[ProviderType, Decimal]:
        totals = {
            ProviderType.SHIPPING: Decimal("0"),
            ProviderType.CARRIER: Decimal("0"),
            ProviderType.INSPECTION: Decimal("0"),
            ProviderType.OTHER: Decimal("0"),
        }
        for charge in charges:
            provider_type = charge.provider_type or ProviderType.OTHER
            totals[provider_type] += charge.amount.amount
        return totals

    def _source_document_url(
        self, invoice_id: UUID, cache: dict[UUID, str | None]
    ) -> str | None:
        if invoice_id in cache:
            return cache[invoice_id]

        client_invoice = self.invoice_repo.find_client_invoice_by_id(invoice_id)
        if client_invoice and client_invoice.source_document is not None:
            url = f"/api/documents/{client_invoice.source_document.document_id}/file"
            cache[invoice_id] = url
            return url

        provider_invoice = self.invoice_repo.find_provider_invoice_by_id(invoice_id)
        if provider_invoice and provider_invoice.source_document is not None:
            url = f"/api/documents/{provider_invoice.source_document.document_id}/file"
            cache[invoice_id] = url
            return url

        cache[invoice_id] = None
        return None
