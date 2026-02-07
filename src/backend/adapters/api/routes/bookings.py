"""Bookings API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.adapters.api.schemas import (
    BookingDetailResponse,
    BookingListItem,
    ListBookingsResponse,
)
from backend.application.dtos import ListBookingsRequest
from backend.application.use_cases import ListBookingsUseCase, ViewBookingDetailUseCase
from backend.config.dependencies import (
    get_list_bookings_use_case,
    get_view_booking_detail_use_case,
)

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.get("", response_model=ListBookingsResponse, status_code=200)
def list_bookings(
    client_id: Annotated[UUID | None, Query(description="Filter by client ID")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    date_from: Annotated[str | None, Query(description="Date from (ISO)")] = None,
    date_to: Annotated[str | None, Query(description="Date to (ISO)")] = None,
    sort_by: Annotated[str, Query(description="Sort field")] = "created_at",
    descending: Annotated[bool, Query(description="Sort descending")] = True,
    use_case: Annotated[ListBookingsUseCase, Depends(get_list_bookings_use_case)] = ...,
) -> ListBookingsResponse:
    """List bookings with filtering and sorting."""
    # Map query params to DTO
    dto_request = ListBookingsRequest(
        client_id=client_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        descending=descending,
    )

    # Execute use case
    bookings = use_case.execute(dto_request)

    # Map DTOs to Pydantic
    return ListBookingsResponse(
        bookings=[
            BookingListItem(
                id=booking.id,
                client_name=booking.client_name,
                created_at=booking.created_at,
                status=booking.status,
                total_revenue=booking.total_revenue,
                total_costs=booking.total_costs,
                margin=booking.margin,
                commission=booking.commission,
                document_count=booking.document_count,
            )
            for booking in bookings
        ],
        total=len(bookings),
    )


@router.get("/{bl_reference}", response_model=BookingDetailResponse, status_code=200)
def get_booking_detail(
    bl_reference: str,
    use_case: Annotated[ViewBookingDetailUseCase, Depends(get_view_booking_detail_use_case)] = ...,
) -> BookingDetailResponse:
    """Get complete booking details by BL reference."""
    # Execute use case
    result = use_case.execute(bl_reference)

    if not result:
        raise HTTPException(status_code=404, detail=f"Booking '{bl_reference}' not found")

    # DTO already matches Pydantic schema
    return BookingDetailResponse(
        id=result.id,
        created_at=result.created_at,
        status=result.status,
        client_id=result.client_id,
        client_name=result.client_name,
        client_nif=result.client_nif,
        pol_code=result.pol_code,
        pol_name=result.pol_name,
        pod_code=result.pod_code,
        pod_name=result.pod_name,
        vessel=result.vessel,
        containers=result.containers,
        total_revenue=result.total_revenue,
        total_costs=result.total_costs,
        margin=result.margin,
        margin_percentage=result.margin_percentage,
        commission=result.commission,
        revenue_charge_count=result.revenue_charge_count,
        cost_charge_count=result.cost_charge_count,
    )
