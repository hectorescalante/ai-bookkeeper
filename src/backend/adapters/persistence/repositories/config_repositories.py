"""SQLite repositories for configuration entities (singletons)."""

from sqlalchemy.orm import Session

from backend.adapters.persistence.mappers import (
    agent_to_model,
    company_to_model,
    model_to_agent,
    model_to_company,
    model_to_settings,
    settings_to_model,
)
from backend.adapters.persistence.models.configuration import (
    AgentModel,
    CompanyModel,
    SettingsModel,
)
from backend.domain.entities.configuration import Agent, Company, Settings
from backend.ports.output.repositories import AgentRepository, CompanyRepository, SettingsRepository


class SqlAlchemyCompanyRepository(CompanyRepository):
    """SQLite implementation of CompanyRepository (singleton)."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, company: Company) -> None:
        """Save or update company configuration."""
        # Check if company already exists
        existing = self.session.query(CompanyModel).first()

        if existing:
            # Update existing
            existing.name = company.name
            existing.nif = company.nif
            existing.agent_commission_rate = company.agent_commission_rate
        else:
            # Create new
            model = company_to_model(company)
            self.session.add(model)

        self.session.commit()

    def get(self) -> Company | None:
        """Get company configuration (singleton)."""
        model = self.session.query(CompanyModel).first()
        if model is None:
            return None
        return model_to_company(model)


class SqlAlchemyAgentRepository(AgentRepository):
    """SQLite implementation of AgentRepository (singleton)."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, agent: Agent) -> None:
        """Save or update agent profile."""
        # Check if agent already exists
        existing = self.session.query(AgentModel).first()

        if existing:
            # Update existing
            existing.name = agent.name
            existing.email = agent.email
            existing.phone = agent.phone
        else:
            # Create new
            model = agent_to_model(agent)
            self.session.add(model)

        self.session.commit()

    def get(self) -> Agent | None:
        """Get agent profile (singleton)."""
        model = self.session.query(AgentModel).first()
        if model is None:
            return None
        return model_to_agent(model)


class SqlAlchemySettingsRepository(SettingsRepository):
    """SQLite implementation of SettingsRepository (singleton)."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, settings: Settings) -> None:
        """Save or update application settings."""
        # Check if settings already exist
        existing = self.session.query(SettingsModel).first()

        if existing:
            # Update existing
            existing.anthropic_api_key = settings.anthropic_api_key
            existing.outlook_configured = settings.outlook_configured
            existing.outlook_refresh_token = settings.outlook_refresh_token
            existing.default_export_path = settings.default_export_path
            existing.extraction_prompt = settings.extraction_prompt
        else:
            # Create new
            model = settings_to_model(settings)
            self.session.add(model)

        self.session.commit()

    def get(self) -> Settings | None:
        """Get application settings (singleton)."""
        model = self.session.query(SettingsModel).first()
        if model is None:
            return None
        return model_to_settings(model)
