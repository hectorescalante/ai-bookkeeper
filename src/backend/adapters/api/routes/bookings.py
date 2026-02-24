"""Bookings API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from backend.adapters.api.schemas import (
    BookingDetailResponse,
    BookingListItem,
    ListBookingsResponse,
)
from backend.application.dtos import EditBookingRequest, ListBookingsRequest
from backend.application.use_cases import (
    EditBookingUseCase,
    ExportBookingUseCase,
    ListBookingsUseCase,
    MarkBookingCompleteUseCase,
    ViewBookingDetailUseCase,
)
from backend.config.dependencies import (
    get_edit_booking_use_case,
    get_export_booking_use_case,
    get_list_bookings_use_case,
    get_mark_booking_complete_use_case,
    get_view_booking_detail_use_case,
)

router = APIRouter(prefix="/api/bookings", tags=["bookings"])
_EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class UpdateBookingRequest(BaseModel):
    """Mutable fields allowed in booking edit flow."""

    vessel: str | None = None
    containers: list[str] | None = None
    pol_code: str | None = Field(None, max_length=10)
    pol_name: str | None = Field(None, max_length=255)
    pod_code: str | None = Field(None, max_length=10)
    pod_name: str | None = Field(None, max_length=255)


@router.get("", response_model=ListBookingsResponse, status_code=200)
def list_bookings(
    client_id: Annotated[UUID | None, Query(description="Filter by client ID")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    date_from: Annotated[str | None, Query(description="Date from (ISO)")] = None,
    date_to: Annotated[str | None, Query(description="Date to (ISO)")] = None,
    sort_by: Annotated[str, Query(description="Sort field")] = "created_at",
    descending: Annotated[bool, Query(description="Sort descending")] = True,
    *,
    use_case: Annotated[ListBookingsUseCase, Depends(get_list_bookings_use_case)],
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


@router.patch("/{bl_reference}", response_model=BookingDetailResponse, status_code=200)
def edit_booking(
    bl_reference: str,
    request: UpdateBookingRequest,
    edit_use_case: Annotated[EditBookingUseCase, Depends(get_edit_booking_use_case)],
    detail_use_case: Annotated[
        ViewBookingDetailUseCase, Depends(get_view_booking_detail_use_case)
    ],
) -> BookingDetailResponse:
    """Edit mutable booking fields."""
    try:
        edit_use_case.execute(
            EditBookingRequest(
                bl_reference=bl_reference,
                vessel=request.vessel,
                containers=request.containers,
                pol_code=request.pol_code,
                pol_name=request.pol_name,
                pod_code=request.pod_code,
                pod_name=request.pod_name,
            )
        )
        return _build_booking_detail_or_404(bl_reference, detail_use_case)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/{bl_reference}/complete", response_model=BookingDetailResponse, status_code=200)
def mark_booking_complete(
    bl_reference: str,
    status_use_case: Annotated[
        MarkBookingCompleteUseCase, Depends(get_mark_booking_complete_use_case)
    ],
    detail_use_case: Annotated[
        ViewBookingDetailUseCase, Depends(get_view_booking_detail_use_case)
    ],
) -> BookingDetailResponse:
    """Mark booking as COMPLETE."""
    try:
        status_use_case.mark_complete(bl_reference)
        return _build_booking_detail_or_404(bl_reference, detail_use_case)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{bl_reference}/revert", response_model=BookingDetailResponse, status_code=200)
def revert_booking_to_pending(
    bl_reference: str,
    status_use_case: Annotated[
        MarkBookingCompleteUseCase, Depends(get_mark_booking_complete_use_case)
    ],
    detail_use_case: Annotated[
        ViewBookingDetailUseCase, Depends(get_view_booking_detail_use_case)
    ],
) -> BookingDetailResponse:
    """Revert booking status back to PENDING."""
    try:
        status_use_case.revert_to_pending(bl_reference)
        return _build_booking_detail_or_404(bl_reference, detail_use_case)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{bl_reference}/export", status_code=200)
def export_booking(
    bl_reference: str,
    use_case: Annotated[ExportBookingUseCase, Depends(get_export_booking_use_case)],
) -> Response:
    """Export a single booking detail as Excel."""
    try:
        file_content = use_case.execute(bl_reference)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    file_name = f"booking-{bl_reference}.xlsx"
    return Response(
        content=file_content,
        media_type=_EXCEL_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/{bl_reference}", response_model=BookingDetailResponse, status_code=200)
def get_booking_detail(
    bl_reference: str,
    use_case: Annotated[
        ViewBookingDetailUseCase, Depends(get_view_booking_detail_use_case)
    ],
) -> BookingDetailResponse:
    """Get complete booking details by BL reference."""
    return _build_booking_detail_or_404(bl_reference, use_case)


def _build_booking_detail_or_404(
    bl_reference: str,
    use_case: ViewBookingDetailUseCase,
) -> BookingDetailResponse:
    """Resolve booking detail from use case or raise 404."""
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
