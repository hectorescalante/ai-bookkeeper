"""Reports API routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from backend.adapters.api.schemas.report_schemas import (
    CommissionReportItem,
    CommissionReportRequest,
    CommissionReportResponse,
    CommissionReportTotals,
    ExportReportRequest,
)
from backend.application.dtos import CommissionReportRequest as CommissionReportRequestDto
from backend.application.use_cases import (
    GenerateCommissionReportUseCase,
    GenerateExcelReportUseCase,
)
from backend.config.dependencies import (
    get_generate_commission_report_use_case,
    get_generate_excel_report_use_case,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

_EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.post("/commission", response_model=CommissionReportResponse, status_code=200)
def generate_commission_report(
    request: CommissionReportRequest,
    use_case: Annotated[
        GenerateCommissionReportUseCase, Depends(get_generate_commission_report_use_case)
    ],
) -> CommissionReportResponse:
    """Generate commission report preview data."""
    try:
        dto_request = CommissionReportRequestDto(
            date_from=request.date_from,
            date_to=request.date_to,
            status=request.status,
        )
        result = use_case.execute(dto_request)
        return CommissionReportResponse(
            items=[
                CommissionReportItem(
                    booking_id=row.booking_id,
                    client_name=row.client_name,
                    created_at=row.created_at,
                    status=row.status,
                    total_revenue=row.total_revenue,
                    total_costs=row.total_costs,
                    margin=row.margin,
                    commission=row.commission,
                )
                for row in result.items
            ],
            totals=CommissionReportTotals(
                booking_count=result.totals.booking_count,
                total_revenue=result.totals.total_revenue,
                total_costs=result.totals.total_costs,
                total_margin=result.totals.total_margin,
                total_commission=result.totals.total_commission,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/export", status_code=200)
def export_commission_report(
    request: ExportReportRequest,
    use_case: Annotated[GenerateExcelReportUseCase, Depends(get_generate_excel_report_use_case)],
) -> Response:
    """Export commission report as an Excel file."""
    try:
        dto_request = CommissionReportRequestDto(
            date_from=request.date_from,
            date_to=request.date_to,
            status=request.status,
        )
        file_content = use_case.execute(dto_request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_name = (request.file_name or "").strip()
    if not file_name:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_name = f"commission-report-{timestamp}.xlsx"
    elif not file_name.lower().endswith(".xlsx"):
        file_name = f"{file_name}.xlsx"

    return Response(
        content=file_content,
        media_type=_EXCEL_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
