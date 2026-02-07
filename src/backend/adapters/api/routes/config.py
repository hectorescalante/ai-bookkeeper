"""Configuration API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from backend.adapters.api.schemas import (
    CompanyRequest,
    CompanyResponse,
    SettingsRequest,
    SettingsResponse,
)
from backend.application.dtos import (
    ConfigureCompanyRequest,
    ConfigureSettingsRequest,
)
from backend.application.use_cases import ConfigureCompanyUseCase, ConfigureSettingsUseCase
from backend.config.dependencies import (
    get_configure_company_use_case,
    get_configure_settings_use_case,
)

router = APIRouter(prefix="/api/config", tags=["configuration"])


@router.post("/company", response_model=CompanyResponse, status_code=200)
def configure_company(
    request: CompanyRequest,
    use_case: Annotated[ConfigureCompanyUseCase, Depends(get_configure_company_use_case)],
) -> CompanyResponse:
    """Configure or update company information."""
    # Map Pydantic to DTO
    dto_request = ConfigureCompanyRequest(
        name=request.name,
        nif=request.nif,
        commission_rate=request.commission_rate,
    )

    # Execute use case
    result = use_case.execute(dto_request)

    # Map DTO to Pydantic
    return CompanyResponse(
        id=result.id,
        name=result.name,
        nif=result.nif,
        commission_rate=result.commission_rate,
        is_configured=result.is_configured,
    )


@router.get("/company", response_model=CompanyResponse, status_code=200)
def get_company(
    use_case: Annotated[ConfigureCompanyUseCase, Depends(get_configure_company_use_case)],
) -> CompanyResponse:
    """Get current company configuration."""
    result = use_case.get_company()

    if not result:
        raise HTTPException(status_code=404, detail="Company not configured")

    return CompanyResponse(
        id=result.id,
        name=result.name,
        nif=result.nif,
        commission_rate=result.commission_rate,
        is_configured=result.is_configured,
    )


@router.post("/settings", response_model=SettingsResponse, status_code=200)
def configure_settings(
    request: SettingsRequest,
    use_case: Annotated[ConfigureSettingsUseCase, Depends(get_configure_settings_use_case)],
) -> SettingsResponse:
    """Configure or update application settings."""
    # Map Pydantic to DTO
    dto_request = ConfigureSettingsRequest(
        anthropic_api_key=request.anthropic_api_key,
        default_export_path=request.default_export_path,
        extraction_prompt=request.extraction_prompt,
    )

    # Execute use case
    result = use_case.execute(dto_request)

    # Map DTO to Pydantic
    return SettingsResponse(
        id=result.id,
        has_api_key=result.has_api_key,
        outlook_configured=result.outlook_configured,
        default_export_path=result.default_export_path,
        extraction_prompt=result.extraction_prompt,
    )


@router.get("/settings", response_model=SettingsResponse, status_code=200)
def get_settings(
    use_case: Annotated[ConfigureSettingsUseCase, Depends(get_configure_settings_use_case)],
) -> SettingsResponse:
    """Get current application settings."""
    result = use_case.get_settings()

    if not result:
        raise HTTPException(status_code=404, detail="Settings not configured")

    return SettingsResponse(
        id=result.id,
        has_api_key=result.has_api_key,
        outlook_configured=result.outlook_configured,
        default_export_path=result.default_export_path,
        extraction_prompt=result.extraction_prompt,
    )
