"""Use case for configuring company information."""

from backend.application.dtos import CompanyResponse, ConfigureCompanyRequest
from backend.domain.entities.configuration import Company
from backend.ports.output.repositories import CompanyRepository


class ConfigureCompanyUseCase:
    """Configure or update company information."""

    def __init__(self, company_repo: CompanyRepository):
        self.company_repo = company_repo

    def execute(self, request: ConfigureCompanyRequest) -> CompanyResponse:
        """Execute the use case."""
        # Get existing or create new
        company = self.company_repo.get()

        if company:
            # Update existing
            company.update(
                name=request.name,
                nif=request.nif,
                commission_rate=request.commission_rate,
            )
        else:
            # Create new
            company = Company.create(
                name=request.name,
                nif=request.nif,
                commission_rate=request.commission_rate,
            )

        self.company_repo.save(company)

        return CompanyResponse(
            id=company.id,
            name=company.name,
            nif=company.nif,
            commission_rate=company.agent_commission_rate,
            is_configured=company.is_configured,
        )

    def get_company(self) -> CompanyResponse | None:
        """Get current company configuration."""
        company = self.company_repo.get()

        if not company:
            return None

        return CompanyResponse(
            id=company.id,
            name=company.name,
            nif=company.nif,
            commission_rate=company.agent_commission_rate,
            is_configured=company.is_configured,
        )
