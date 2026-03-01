"""Mappers for configuration entities (Company, Agent, Settings)."""

from backend.adapters.persistence.models.configuration import (
    AgentModel,
    CompanyModel,
    SettingsModel,
)
from backend.domain.entities.configuration import Agent, Company, Settings


def company_to_model(company: Company) -> CompanyModel:
    """Convert Company entity to CompanyModel ORM."""
    return CompanyModel(
        id=company.id,
        name=company.name,
        nif=company.nif,
        address=company.address,
        contact_info=company.contact_info,
        agent_commission_rate=company.agent_commission_rate,
    )


def model_to_company(model: CompanyModel) -> Company:
    """Convert CompanyModel ORM to Company entity."""
    return Company(
        id=model.id,
        name=model.name,
        nif=model.nif,
        address=model.address,
        contact_info=model.contact_info,
        agent_commission_rate=model.agent_commission_rate,
    )


def agent_to_model(agent: Agent) -> AgentModel:
    """Convert Agent entity to AgentModel ORM."""
    return AgentModel(
        id=agent.id,
        name=agent.name,
        email=agent.email,
        phone=agent.phone,
    )


def model_to_agent(model: AgentModel) -> Agent:
    """Convert AgentModel ORM to Agent entity."""
    return Agent(
        id=model.id,
        name=model.name,
        email=model.email,
        phone=model.phone,
    )


def settings_to_model(settings: Settings) -> SettingsModel:
    """Convert Settings entity to SettingsModel ORM."""
    return SettingsModel(
        id=settings.id,
        gemini_api_key=settings.gemini_api_key,
        outlook_configured=settings.outlook_configured,
        outlook_refresh_token=settings.outlook_refresh_token,
        default_export_path=settings.default_export_path,
        extraction_prompt=settings.extraction_prompt,
        onboarding_dismissed=settings.onboarding_dismissed,
    )


def model_to_settings(model: SettingsModel) -> Settings:
    """Convert SettingsModel ORM to Settings entity."""
    return Settings(
        id=model.id,
        gemini_api_key=model.gemini_api_key,
        outlook_configured=model.outlook_configured,
        outlook_refresh_token=model.outlook_refresh_token,
        default_export_path=model.default_export_path,
        extraction_prompt=model.extraction_prompt,
        onboarding_dismissed=model.onboarding_dismissed,
    )
