"""Use case for viewing booking details."""

from decimal import Decimal

from backend.application.dtos import BookingDetailResponse
from backend.ports.output.repositories import BookingRepository


class ViewBookingDetailUseCase:
    """View complete booking details."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        company_commission_rate: Decimal = Decimal("0.50"),
    ):
        self.booking_repo = booking_repo
        self.commission_rate = company_commission_rate

    def execute(self, bl_reference: str) -> BookingDetailResponse | None:
        """Execute the use case."""
        # Find booking
        booking = self.booking_repo.find_by_id(bl_reference)

        if not booking:
            return None

        # Convert to DTO
        return BookingDetailResponse(
            id=booking.id,
            created_at=booking.created_at,
            status=booking.status.value,
            client_id=booking.client.id if booking.client else None,
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
            margin=booking.margin.amount,
            margin_percentage=booking.margin_percentage,
            commission=booking.calculate_agent_commission(self.commission_rate).amount,
            revenue_charge_count=len(booking.revenue_charges),
            cost_charge_count=len(booking.cost_charges),
        )
