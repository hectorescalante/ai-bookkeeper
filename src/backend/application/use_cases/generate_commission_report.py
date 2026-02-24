"""Use case for generating commission report data."""

from datetime import date
from decimal import Decimal

from backend.application.dtos import (
    CommissionReportItem,
    CommissionReportRequest,
    CommissionReportResponse,
    CommissionReportTotals,
)
from backend.domain.enums import BookingStatus
from backend.ports.output.repositories import (
    BookingFilters,
    BookingRepository,
    BookingSort,
    CompanyRepository,
)


class GenerateCommissionReportUseCase:
    """Generate commission report rows and totals."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        company_repo: CompanyRepository,
    ) -> None:
        self.booking_repo = booking_repo
        self.company_repo = company_repo

    def execute(self, request: CommissionReportRequest) -> CommissionReportResponse:
        """Build report data from bookings filtered by date and status."""
        self._validate_dates(request.date_from, request.date_to)

        status = self._parse_status(request.status)
        filters = BookingFilters(
            status=status,
            date_from=request.date_from,
            date_to=request.date_to,
        )
        sort = BookingSort(field="created_at", descending=False)
        bookings = self.booking_repo.list_all(filters=filters, sort=sort)

        company = self.company_repo.get()
        commission_rate = company.agent_commission_rate if company else Decimal("0.50")

        rows = [
            CommissionReportItem(
                booking_id=booking.id,
                client_name=booking.client.name if booking.client else None,
                created_at=booking.created_at,
                status=booking.status.value,
                total_revenue=booking.total_revenue.amount,
                total_costs=booking.total_costs.amount,
                margin=booking.margin.amount,
                commission=booking.calculate_agent_commission(commission_rate).amount,
            )
            for booking in bookings
        ]

        totals = CommissionReportTotals(
            booking_count=len(rows),
            total_revenue=sum((row.total_revenue for row in rows), Decimal("0.00")),
            total_costs=sum((row.total_costs for row in rows), Decimal("0.00")),
            total_margin=sum((row.margin for row in rows), Decimal("0.00")),
            total_commission=sum((row.commission for row in rows), Decimal("0.00")),
        )
        return CommissionReportResponse(items=rows, totals=totals)

    @staticmethod
    def _parse_status(status: str | None) -> BookingStatus | None:
        if status is None or not status.strip():
            return None
        normalized = status.strip().upper()
        try:
            return BookingStatus[normalized]
        except KeyError as exc:
            raise ValueError(f"Invalid status: {status}") from exc

    @staticmethod
    def _validate_dates(date_from: str | None, date_to: str | None) -> None:
        parsed_from = date.fromisoformat(date_from) if date_from else None
        parsed_to = date.fromisoformat(date_to) if date_to else None
        if parsed_from and parsed_to and parsed_from > parsed_to:
            raise ValueError("date_from cannot be greater than date_to")
