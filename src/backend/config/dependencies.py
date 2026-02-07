"""Dependency injection for FastAPI."""

from decimal import Decimal
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import get_db
from backend.adapters.persistence.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyClientRepository,
    SqlAlchemyCompanyRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyProviderRepository,
    SqlAlchemySettingsRepository,
)
from backend.application.use_cases import (
    ConfigureCompanyUseCase,
    ConfigureSettingsUseCase,
    ListBookingsUseCase,
    ListDocumentsUseCase,
    ViewBookingDetailUseCase,
)
from backend.ports.output.repositories import (
    BookingRepository,
    ClientRepository,
    CompanyRepository,
    DocumentRepository,
    ProviderRepository,
    SettingsRepository,
)

# --- Repository Dependencies ---


def get_company_repository(db: Annotated[Session, Depends(get_db)]) -> CompanyRepository:
    """Get company repository instance."""
    return SqlAlchemyCompanyRepository(db)


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


# --- Use Case Dependencies ---


def get_configure_company_use_case(
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> ConfigureCompanyUseCase:
    """Get configure company use case instance."""
    return ConfigureCompanyUseCase(company_repo)


def get_configure_settings_use_case(
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> ConfigureSettingsUseCase:
    """Get configure settings use case instance."""
    return ConfigureSettingsUseCase(settings_repo)


def get_list_documents_use_case(
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> ListDocumentsUseCase:
    """Get list documents use case instance."""
    return ListDocumentsUseCase(document_repo)


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
