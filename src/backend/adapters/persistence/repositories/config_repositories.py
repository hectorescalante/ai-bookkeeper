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
from backend.adapters.security import OutlookRefreshTokenVault
from backend.domain.entities.configuration import Agent, Company, Settings
from backend.ports.output.repositories import AgentRepository, CompanyRepository, SettingsRepository


class SqlAlchemyCompanyRepository(CompanyRepository):
    """SQLite implementation of CompanyRepository (singleton)."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, company: Company) -> None:
        """Save or update company configuration."""
        existing = self.session.query(CompanyModel).first()

        if existing:
            existing.name = company.name
            existing.nif = company.nif
            existing.agent_commission_rate = company.agent_commission_rate
        else:
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
        existing = self.session.query(AgentModel).first()

        if existing:
            existing.name = agent.name
            existing.email = agent.email
            existing.phone = agent.phone
        else:
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
        self._token_vault = OutlookRefreshTokenVault()

    def save(self, settings: Settings) -> None:
        """Save or update application settings."""
        existing = self.session.query(SettingsModel).first()
        previous_stored_token = existing.outlook_refresh_token if existing else ""
        stored_token_value = self._prepare_stored_refresh_token(
            settings=settings,
            previous_stored_token=previous_stored_token,
        )

        if existing:
            existing.gemini_api_key = settings.gemini_api_key
            existing.outlook_configured = settings.outlook_configured
            existing.outlook_refresh_token = stored_token_value
            existing.default_export_path = settings.default_export_path
            existing.extraction_prompt = settings.extraction_prompt
        else:
            model = settings_to_model(settings)
            model.outlook_refresh_token = stored_token_value
            self.session.add(model)

        self.session.commit()

    def get(self) -> Settings | None:
        """Get application settings (singleton)."""
        model = self.session.query(SettingsModel).first()
        if model is None:
            return None
        settings = model_to_settings(model)
        stored_token = model.outlook_refresh_token
        resolved_token = self._token_vault.load_token(
            settings.id,
            stored_token,
        )
        if not settings.outlook_configured:
            settings.outlook_refresh_token = ""
            return settings

        settings.outlook_refresh_token = resolved_token
        if not resolved_token or self._token_vault.is_keychain_reference(stored_token):
            return settings

        try:
            migrated_token_reference = self._token_vault.save_token(settings.id, resolved_token)
        except RuntimeError:
            return settings
        if migrated_token_reference and migrated_token_reference != stored_token:
            model.outlook_refresh_token = migrated_token_reference
            self.session.commit()

        settings.outlook_refresh_token = resolved_token
        return settings

    def _prepare_stored_refresh_token(
        self,
        settings: Settings,
        previous_stored_token: str,
    ) -> str:
        if settings.outlook_configured and settings.outlook_refresh_token:
            return self._token_vault.save_token(
                settings.id,
                settings.outlook_refresh_token,
            )
        self._token_vault.delete_token(settings.id, previous_stored_token)
        return ""
