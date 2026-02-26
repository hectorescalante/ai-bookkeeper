"""Use case for listing bookings."""

from decimal import Decimal

from backend.application.dtos import BookingListItem, ListBookingsRequest
from backend.domain.enums import BookingStatus
from backend.ports.output.repositories import BookingFilters, BookingRepository, BookingSort


class ListBookingsUseCase:
    """List bookings with filtering and sorting."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        company_commission_rate: Decimal = Decimal("0.50"),
    ):
        self.booking_repo = booking_repo
        self.commission_rate = company_commission_rate

    def execute(self, request: ListBookingsRequest) -> list[BookingListItem]:
        """Execute the use case."""
        # Build filters
        booking_filter = request.booking.strip() if request.booking else None
        filters = BookingFilters(
            client_id=request.client_id,
            booking=booking_filter or None,
            status=BookingStatus[request.status.upper()] if request.status else None,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        # Build sort
        sort = BookingSort(
            field=request.sort_by,
            descending=request.descending,
        )

        # Query bookings
        bookings = self.booking_repo.list_all(filters=filters, sort=sort)

        if request.client is not None:
            normalized_client = request.client.strip().lower()
            if normalized_client:
                bookings = [
                    booking
                    for booking in bookings
                    if booking.client is not None
                    and normalized_client in booking.client.name.lower()
                ]

        # Convert to DTOs
        items = [
            BookingListItem(
                id=booking.id,
                client_name=booking.client.name if booking.client else None,
                pol_code=booking.pol.code if booking.pol else None,
                pod_code=booking.pod.code if booking.pod else None,
                created_at=booking.created_at,
                status=booking.status.value,
                total_revenue=booking.total_revenue.amount,
                total_costs=booking.total_costs.amount,
                margin=booking.margin.amount,
                commission=booking.calculate_agent_commission(self.commission_rate).amount,
                document_count=len(booking.revenue_charges) + len(booking.cost_charges),
            )
            for booking in bookings
        ]

        sort_fields = {
            "created_at": lambda item: item.created_at,
            "margin": lambda item: item.margin,
            "commission": lambda item: item.commission,
        }
        sort_key = sort_fields.get(request.sort_by)
        if sort_key is not None:
            items.sort(key=sort_key, reverse=request.descending)

        return items
