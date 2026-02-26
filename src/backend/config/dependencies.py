"""Dependency injection for FastAPI."""

from decimal import Decimal
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.adapters.ai import GeminiExtractor
from backend.adapters.email import OutlookGraphEmailClient, OutlookOAuthManager
from backend.adapters.persistence.database import get_db
from backend.adapters.persistence.repositories import (
    SqlAlchemyAgentRepository,
    SqlAlchemyBookingRepository,
    SqlAlchemyClientRepository,
    SqlAlchemyCompanyRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyInvoiceRepository,
    SqlAlchemyProviderRepository,
    SqlAlchemySettingsRepository,
)
from backend.application.use_cases import (
    ConfigureAgentUseCase,
    ConfigureCompanyUseCase,
    ConfigureSettingsUseCase,
    ConfirmInvoiceUseCase,
    EditBookingUseCase,
    ExportBookingUseCase,
    FetchEmailsUseCase,
    GenerateCommissionReportUseCase,
    GenerateExcelReportUseCase,
    ListBookingsUseCase,
    ListDocumentsUseCase,
    MarkBookingCompleteUseCase,
    ViewBookingDetailUseCase,
)
from backend.application.use_cases.process_invoice import ProcessInvoiceUseCase
from backend.config import get_settings
from backend.ports.output.ai_extractor import AIExtractor
from backend.ports.output.email_client import EmailClient
from backend.ports.output.repositories import (
    AgentRepository,
    BookingRepository,
    ClientRepository,
    CompanyRepository,
    DocumentRepository,
    InvoiceRepository,
    ProviderRepository,
    SettingsRepository,
)

_oauth_manager: OutlookOAuthManager | None = None

# --- Repository Dependencies ---


def get_company_repository(db: Annotated[Session, Depends(get_db)]) -> CompanyRepository:
    """Get company repository instance."""
    return SqlAlchemyCompanyRepository(db)

def get_agent_repository(db: Annotated[Session, Depends(get_db)]) -> AgentRepository:
    """Get agent repository instance."""
    return SqlAlchemyAgentRepository(db)


def get_settings_repository(db: Annotated[Session, Depends(get_db)]) -> SettingsRepository:
    """Get settings repository instance."""
    return SqlAlchemySettingsRepository(db)


def get_document_repository(db: Annotated[Session, Depends(get_db)]) -> DocumentRepository:
    """Get document repository instance."""
    return SqlAlchemyDocumentRepository(db)


def get_booking_repository(db: Annotated[Session, Depends(get_db)]) -> BookingRepository:
    """Get booking repository instance."""
    return SqlAlchemyBookingRepository(db)


def get_client_repository(db: Annotated[Session, Depends(get_db)]) -> ClientRepository:
    """Get client repository instance."""
    return SqlAlchemyClientRepository(db)


def get_provider_repository(db: Annotated[Session, Depends(get_db)]) -> ProviderRepository:
    """Get provider repository instance."""
    return SqlAlchemyProviderRepository(db)


def get_invoice_repository(db: Annotated[Session, Depends(get_db)]) -> InvoiceRepository:
    """Get invoice repository instance."""
    return SqlAlchemyInvoiceRepository(db)


# --- Use Case Dependencies ---


def get_configure_company_use_case(
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> ConfigureCompanyUseCase:
    """Get configure company use case instance."""
    return ConfigureCompanyUseCase(company_repo)

def get_configure_agent_use_case(
    agent_repo: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> ConfigureAgentUseCase:
    """Get configure agent use case instance."""
    return ConfigureAgentUseCase(agent_repo)


def get_configure_settings_use_case(
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> ConfigureSettingsUseCase:
    """Get configure settings use case instance."""
    return ConfigureSettingsUseCase(settings_repo)


def get_list_documents_use_case(
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
    invoice_repo: Annotated[InvoiceRepository, Depends(get_invoice_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    provider_repo: Annotated[ProviderRepository, Depends(get_provider_repository)],
) -> ListDocumentsUseCase:
    """Get list documents use case instance."""
    return ListDocumentsUseCase(
        document_repo=document_repo,
        invoice_repo=invoice_repo,
        client_repo=client_repo,
        provider_repo=provider_repo,
    )


def get_list_bookings_use_case(
    booking_repo: Annotated[BookingRepository, Depends(get_booking_repository)],
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> ListBookingsUseCase:
    """Get list bookings use case instance."""
    # Get commission rate from company config, default to 50%
    company = company_repo.get()
    commission_rate = company.agent_commission_rate if company else Decimal("0.50")
    return ListBookingsUseCase(booking_repo, commission_rate)


def get_view_booking_detail_use_case(
    booking_repo: Annotated[BookingRepository, Depends(get_booking_repository)],
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> ViewBookingDetailUseCase:
    """Get view booking detail use case instance."""
    # Get commission rate from company config, default to 50%
    company = company_repo.get()
    commission_rate = company.agent_commission_rate if company else Decimal("0.50")
    return ViewBookingDetailUseCase(booking_repo, commission_rate)


def get_edit_booking_use_case(
    booking_repo: Annotated[BookingRepository, Depends(get_booking_repository)],
) -> EditBookingUseCase:
    """Get edit booking use case instance."""
    return EditBookingUseCase(booking_repo)


def get_mark_booking_complete_use_case(
    booking_repo: Annotated[BookingRepository, Depends(get_booking_repository)],
) -> MarkBookingCompleteUseCase:
    """Get mark booking complete use case instance."""
    return MarkBookingCompleteUseCase(booking_repo)


def get_export_booking_use_case(
    booking_repo: Annotated[BookingRepository, Depends(get_booking_repository)],
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> ExportBookingUseCase:
    """Get booking export use case instance."""
    return ExportBookingUseCase(
        booking_repo=booking_repo,
        company_repo=company_repo,
    )


def get_ai_extractor(
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> AIExtractor:
    """Get AI extractor instance."""
    settings = settings_repo.get()
    api_key = settings.gemini_api_key if settings else ""
    return GeminiExtractor(api_key=api_key)


def get_email_client(
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> EmailClient:
    """Get Outlook email client adapter."""
    settings = settings_repo.get()
    refresh_token = settings.outlook_refresh_token if settings else ""
    app_settings = get_settings()
    return OutlookGraphEmailClient(
        client_id=app_settings.azure_client_id or "",
        tenant_id=app_settings.azure_tenant_id,
        refresh_token=refresh_token,
        redirect_uri=app_settings.azure_redirect_uri,
    )


def get_outlook_oauth_manager() -> OutlookOAuthManager:
    """Get reusable Outlook OAuth manager instance."""
    global _oauth_manager  # noqa: PLW0603
    app_settings = get_settings()
    client_id = app_settings.azure_client_id or ""
    tenant_id = app_settings.azure_tenant_id
    redirect_uri = app_settings.azure_redirect_uri

    if _oauth_manager is None or (
        _oauth_manager.client_id != client_id
        or _oauth_manager.tenant_id != tenant_id
        or _oauth_manager.redirect_uri != redirect_uri
    ):
        _oauth_manager = OutlookOAuthManager(
            client_id=client_id,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri,
        )

    return _oauth_manager


def get_process_invoice_use_case(
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
    ai_extractor: Annotated[AIExtractor, Depends(get_ai_extractor)],
) -> ProcessInvoiceUseCase:
    """Get process invoice use case instance."""
    return ProcessInvoiceUseCase(
        document_repo=document_repo,
        settings_repo=settings_repo,
        company_repo=company_repo,
        ai_extractor=ai_extractor,
    )


def get_fetch_emails_use_case(
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
    email_client: Annotated[EmailClient, Depends(get_email_client)],
) -> FetchEmailsUseCase:
    """Get fetch emails use case instance."""
    app_settings = get_settings()
    return FetchEmailsUseCase(
        document_repo=document_repo,
        settings_repo=settings_repo,
        email_client=email_client,
        storage_root=app_settings.storage_path,
    )


def get_confirm_invoice_use_case(
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
    booking_repo: Annotated[BookingRepository, Depends(get_booking_repository)],
    invoice_repo: Annotated[InvoiceRepository, Depends(get_invoice_repository)],
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    provider_repo: Annotated[ProviderRepository, Depends(get_provider_repository)],
) -> ConfirmInvoiceUseCase:
    """Get confirm invoice use case instance."""
    return ConfirmInvoiceUseCase(
        document_repo=document_repo,
        booking_repo=booking_repo,
        invoice_repo=invoice_repo,
        client_repo=client_repo,
        provider_repo=provider_repo,
    )


def get_generate_commission_report_use_case(
    booking_repo: Annotated[BookingRepository, Depends(get_booking_repository)],
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> GenerateCommissionReportUseCase:
    """Get commission report use case instance."""
    return GenerateCommissionReportUseCase(
        booking_repo=booking_repo,
        company_repo=company_repo,
    )


def get_generate_excel_report_use_case(
    commission_use_case: Annotated[
        GenerateCommissionReportUseCase, Depends(get_generate_commission_report_use_case)
    ],
) -> GenerateExcelReportUseCase:
    """Get Excel report export use case instance."""
    return GenerateExcelReportUseCase(commission_report_use_case=commission_use_case)
