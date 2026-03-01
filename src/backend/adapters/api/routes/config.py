"""Configuration API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from backend.adapters.api.schemas import (
    AgentRequest,
    AgentResponse,
    CompanyRequest,
    CompanyResponse,
    DiagnosticsExportResponse,
    SettingsRequest,
    SettingsResponse,
    TestGeminiConnectionRequest,
    TestGeminiConnectionResponse,
)
from backend.application.dtos import (
    ConfigureAgentRequest,
    ConfigureCompanyRequest,
    ConfigureSettingsRequest,
)
from backend.application.use_cases import (
    ConfigureAgentUseCase,
    ConfigureCompanyUseCase,
    ConfigureSettingsUseCase,
    ExportDiagnosticsUseCase,
)
from backend.config.dependencies import (
    get_ai_extractor,
    get_configure_agent_use_case,
    get_configure_company_use_case,
    get_configure_settings_use_case,
    get_export_diagnostics_use_case,
    get_settings_repository,
)
from backend.ports.output.ai_extractor import AIExtractor
from backend.ports.output.repositories import SettingsRepository

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
        address=request.address,
        contact_info=request.contact_info,
        commission_rate=request.commission_rate,
    )

    # Execute use case
    result = use_case.execute(dto_request)

    # Map DTO to Pydantic
    return CompanyResponse(
        id=result.id,
        name=result.name,
        nif=result.nif,
        address=result.address,
        contact_info=result.contact_info,
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
        address=result.address,
        contact_info=result.contact_info,
        commission_rate=result.commission_rate,
        is_configured=result.is_configured,
    )

@router.post("/agent", response_model=AgentResponse, status_code=200)
def configure_agent(
    request: AgentRequest,
    use_case: Annotated[ConfigureAgentUseCase, Depends(get_configure_agent_use_case)],
) -> AgentResponse:
    """Configure or update agent profile."""
    dto_request = ConfigureAgentRequest(
        name=request.name,
        email=request.email,
        phone=request.phone,
    )
    result = use_case.execute(dto_request)
    return AgentResponse(
        id=result.id,
        name=result.name,
        email=result.email,
        phone=result.phone,
    )


@router.get("/agent", response_model=AgentResponse, status_code=200)
def get_agent(
    use_case: Annotated[ConfigureAgentUseCase, Depends(get_configure_agent_use_case)],
) -> AgentResponse:
    """Get current agent profile."""
    result = use_case.get_agent()

    if not result:
        raise HTTPException(status_code=404, detail="Agent not configured")

    return AgentResponse(
        id=result.id,
        name=result.name,
        email=result.email,
        phone=result.phone,
    )


@router.post("/settings", response_model=SettingsResponse, status_code=200)
def configure_settings(
    request: SettingsRequest,
    use_case: Annotated[ConfigureSettingsUseCase, Depends(get_configure_settings_use_case)],
) -> SettingsResponse:
    """Configure or update application settings."""
    # Map Pydantic to DTO
    dto_request = ConfigureSettingsRequest(
        gemini_api_key=request.gemini_api_key,
        default_export_path=request.default_export_path,
        extraction_prompt=request.extraction_prompt,
        onboarding_dismissed=request.onboarding_dismissed,
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
        onboarding_dismissed=result.onboarding_dismissed,
    )


@router.post(
    "/diagnostics/export",
    response_model=DiagnosticsExportResponse,
    status_code=200,
)
def export_diagnostics(
    use_case: Annotated[
        ExportDiagnosticsUseCase,
        Depends(get_export_diagnostics_use_case),
    ],
) -> DiagnosticsExportResponse:
    """Generate a diagnostics bundle for support sharing."""
    result = use_case.execute()
    return DiagnosticsExportResponse(
        bundle_name=result.bundle_name,
        bundle_path=result.bundle_path,
        created_at=result.created_at,
        warnings=result.warnings,
    )


@router.post(
    "/settings/test-connection",
    response_model=TestGeminiConnectionResponse,
    status_code=200,
)
def test_gemini_connection(
    request: TestGeminiConnectionRequest,
    ai_extractor: Annotated[AIExtractor, Depends(get_ai_extractor)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> TestGeminiConnectionResponse:
    """Validate Gemini API key by making a test request."""
    api_key = (request.gemini_api_key or "").strip()
    if not api_key:
        settings = settings_repo.get()
        api_key = (settings.gemini_api_key if settings else "").strip()

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key is required to test connection.",
        )

    if not ai_extractor.test_connection(api_key):
        raise HTTPException(
            status_code=400,
            detail="Invalid Gemini API key. Please verify it and retry.",
        )

    return TestGeminiConnectionResponse(valid=True, message="Valid connection")


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
        onboarding_dismissed=result.onboarding_dismissed,
    )
