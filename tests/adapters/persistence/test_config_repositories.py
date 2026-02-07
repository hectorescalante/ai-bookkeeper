"""Integration tests for configuration repositories (singletons)."""

from decimal import Decimal

from backend.adapters.persistence.repositories import (
    SqlAlchemyAgentRepository,
    SqlAlchemyCompanyRepository,
    SqlAlchemySettingsRepository,
)
from backend.domain.entities.configuration import Agent, Company, Settings


class TestCompanyRepository:
    """Test suite for SqlAlchemyCompanyRepository."""

    def test_save_and_retrieve_company(self, db_session):
        """Test saving and retrieving company configuration."""
        repo = SqlAlchemyCompanyRepository(db_session)

        # Create and save
        company = Company.create(
            name="Test Company SA", nif="B12345678", commission_rate=Decimal("0.50")
        )
        repo.save(company)

        # Retrieve
        retrieved = repo.get()

        assert retrieved is not None
        assert retrieved.name == "Test Company SA"
        assert retrieved.nif == "B12345678"
        assert retrieved.agent_commission_rate == Decimal("0.50")

    def test_update_existing_company(self, db_session):
        """Test that saving again updates existing record (singleton)."""
        repo = SqlAlchemyCompanyRepository(db_session)

        # Create first
        company1 = Company.create(name="Company 1", nif="B11111111")
        repo.save(company1)

        # Update with new data
        company2 = Company.create(
            name="Company 2 Updated", nif="B22222222", commission_rate=Decimal("0.45")
        )
        company2.id = company1.id  # Same ID
        repo.save(company2)

        # Should only have one record
        retrieved = repo.get()
        assert retrieved is not None
        assert retrieved.name == "Company 2 Updated"
        assert retrieved.nif == "B22222222"
        assert retrieved.agent_commission_rate == Decimal("0.45")

    def test_get_empty_returns_none(self, db_session):
        """Test that get returns None when no company exists."""
        repo = SqlAlchemyCompanyRepository(db_session)

        result = repo.get()

        assert result is None


class TestAgentRepository:
    """Test suite for SqlAlchemyAgentRepository."""

    def test_save_and_retrieve_agent(self, db_session):
        """Test saving and retrieving agent profile."""
        repo = SqlAlchemyAgentRepository(db_session)

        # Create and save
        agent = Agent.create(name="John Doe", email="john@example.com", phone="+34612345678")
        repo.save(agent)

        # Retrieve
        retrieved = repo.get()

        assert retrieved is not None
        assert retrieved.name == "John Doe"
        assert retrieved.email == "john@example.com"
        assert retrieved.phone == "+34612345678"

    def test_update_existing_agent(self, db_session):
        """Test updating agent profile."""
        repo = SqlAlchemyAgentRepository(db_session)

        # Create first
        agent1 = Agent.create(name="Agent 1", email="old@example.com")
        repo.save(agent1)

        # Update
        agent2 = Agent.create(name="Agent Updated", email="new@example.com", phone="+34999")
        agent2.id = agent1.id
        repo.save(agent2)

        # Retrieve
        retrieved = repo.get()
        assert retrieved is not None
        assert retrieved.name == "Agent Updated"
        assert retrieved.email == "new@example.com"
        assert retrieved.phone == "+34999"


class TestSettingsRepository:
    """Test suite for SqlAlchemySettingsRepository."""

    def test_save_and_retrieve_settings(self, db_session):
        """Test saving and retrieving application settings."""
        repo = SqlAlchemySettingsRepository(db_session)

        # Create and save
        settings = Settings.create()
        settings.set_api_key("sk-ant-test-key")
        settings.set_outlook_configured(True, "refresh_token_abc")
        settings.extraction_prompt = "Custom prompt template"

        repo.save(settings)

        # Retrieve
        retrieved = repo.get()

        assert retrieved is not None
        assert retrieved.anthropic_api_key == "sk-ant-test-key"
        assert retrieved.outlook_configured is True
        assert retrieved.outlook_refresh_token == "refresh_token_abc"
        assert retrieved.extraction_prompt == "Custom prompt template"

    def test_update_settings(self, db_session):
        """Test updating settings."""
        repo = SqlAlchemySettingsRepository(db_session)

        # Create initial
        settings1 = Settings.create()
        settings1.set_api_key("old-key")
        repo.save(settings1)

        # Update
        settings2 = Settings.create()
        settings2.id = settings1.id
        settings2.set_api_key("new-key")
        settings2.default_export_path = "/path/to/exports"
        repo.save(settings2)

        # Retrieve
        retrieved = repo.get()
        assert retrieved is not None
        assert retrieved.anthropic_api_key == "new-key"
        assert retrieved.default_export_path == "/path/to/exports"

    def test_get_empty_returns_none(self, db_session):
        """Test that get returns None when no settings exist."""
        repo = SqlAlchemySettingsRepository(db_session)

        result = repo.get()

        assert result is None
