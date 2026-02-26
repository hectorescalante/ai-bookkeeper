"""Reports API routes."""

from datetime import date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from backend.adapters.api.schemas.report_schemas import (
    CommissionReportItem,
    CommissionReportRequest,
    CommissionReportResponse,
    CommissionReportTotals,
    ExportReportRequest,
    SaveExportResponse,
)
from backend.application.dtos import CommissionReportRequest as CommissionReportRequestDto
from backend.application.use_cases import (
    GenerateCommissionReportUseCase,
    GenerateExcelReportUseCase,
)
from backend.config.dependencies import (
    get_generate_commission_report_use_case,
    get_generate_excel_report_use_case,
    get_settings_repository,
)
from backend.ports.output.repositories import SettingsRepository

router = APIRouter(prefix="/api/reports", tags=["reports"])

_EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _to_iso_date(value: date | None) -> str | None:
    """Convert optional date input to ISO date string."""
    return value.isoformat() if value is not None else None


def _to_commission_request(request: CommissionReportRequest | ExportReportRequest) -> CommissionReportRequestDto:
    """Convert API report request schema to application DTO."""
    return CommissionReportRequestDto(
        date_from=_to_iso_date(request.date_from),
        date_to=_to_iso_date(request.date_to),
        status=request.status,
        client=request.client,
        booking=request.booking,
        invoice_type=request.invoice_type,
    )


def _resolve_file_name(file_name: str | None) -> str:
    """Resolve normalized export file name with .xlsx extension."""
    cleaned = (file_name or "").strip()
    if not cleaned:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"commission-report-{timestamp}.xlsx"
    if not cleaned.lower().endswith(".xlsx"):
        return f"{cleaned}.xlsx"
    return cleaned


@router.post("/commission", response_model=CommissionReportResponse, status_code=200)
def generate_commission_report(
    request: CommissionReportRequest,
    use_case: Annotated[
        GenerateCommissionReportUseCase, Depends(get_generate_commission_report_use_case)
    ],
) -> CommissionReportResponse:
    """Generate commission report preview data."""
    try:
        dto_request = _to_commission_request(request)
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
        dto_request = _to_commission_request(request)
        file_content = use_case.execute(dto_request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    file_name = _resolve_file_name(request.file_name)

    return Response(
        content=file_content,
        media_type=_EXCEL_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.post("/export/save", response_model=SaveExportResponse, status_code=200)
def save_commission_report_to_default_path(
    request: ExportReportRequest,
    use_case: Annotated[GenerateExcelReportUseCase, Depends(get_generate_excel_report_use_case)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> SaveExportResponse:
    """Generate and save report to configured default export path."""
    settings = settings_repo.get()
    default_export_path = (settings.default_export_path if settings else "").strip()
    if not default_export_path:
        raise HTTPException(
            status_code=400,
            detail="default_export_path is not configured",
        )

    try:
        dto_request = _to_commission_request(request)
        file_content = use_case.execute(dto_request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_name = _resolve_file_name(request.file_name)
    export_dir = Path(default_export_path).expanduser()
    export_dir.mkdir(parents=True, exist_ok=True)
    target_path = export_dir / file_name
    target_path.write_bytes(file_content)

    return SaveExportResponse(
        file_name=file_name,
        saved_path=str(target_path),
    )
