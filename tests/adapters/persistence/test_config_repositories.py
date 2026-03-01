"""Integration tests for configuration repositories (singletons)."""

from decimal import Decimal
from uuid import uuid4

from backend.adapters.persistence.models.configuration import SettingsModel
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

        company = Company.create(
            name="Test Company SA",
            nif="B12345678",
            address="Old Port 12, Valencia",
            contact_info="ops@test-company.com",
            commission_rate=Decimal("0.50"),
        )
        repo.save(company)

        retrieved = repo.get()

        assert retrieved is not None
        assert retrieved.name == "Test Company SA"
        assert retrieved.nif == "B12345678"
        assert retrieved.address == "Old Port 12, Valencia"
        assert retrieved.contact_info == "ops@test-company.com"
        assert retrieved.agent_commission_rate == Decimal("0.50")

    def test_update_existing_company(self, db_session):
        """Test that saving again updates existing record (singleton)."""
        repo = SqlAlchemyCompanyRepository(db_session)

        company1 = Company.create(name="Company 1", nif="B11111111")
        repo.save(company1)

        company2 = Company.create(
            name="Company 2 Updated",
            nif="B22222222",
            address="New Dock 5, Barcelona",
            contact_info="finance@company2.com",
            commission_rate=Decimal("0.45"),
        )
        company2.id = company1.id
        repo.save(company2)

        retrieved = repo.get()
        assert retrieved is not None
        assert retrieved.name == "Company 2 Updated"
        assert retrieved.nif == "B22222222"
        assert retrieved.address == "New Dock 5, Barcelona"
        assert retrieved.contact_info == "finance@company2.com"
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

        agent = Agent.create(name="John Doe", email="john@example.com", phone="+34612345678")
        repo.save(agent)

        retrieved = repo.get()

        assert retrieved is not None
        assert retrieved.name == "John Doe"
        assert retrieved.email == "john@example.com"
        assert retrieved.phone == "+34612345678"

    def test_update_existing_agent(self, db_session):
        """Test updating agent profile."""
        repo = SqlAlchemyAgentRepository(db_session)

        agent1 = Agent.create(name="Agent 1", email="old@example.com")
        repo.save(agent1)

        agent2 = Agent.create(name="Agent Updated", email="new@example.com", phone="+34999")
        agent2.id = agent1.id
        repo.save(agent2)

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

        settings = Settings.create()
        settings.set_api_key("test-gemini-key")
        settings.set_outlook_configured(True, "refresh_token_abc")
        settings.extraction_prompt = "Custom prompt template"
        settings.set_onboarding_dismissed(True)

        repo.save(settings)

        retrieved = repo.get()

        assert retrieved is not None
        assert retrieved.gemini_api_key == "test-gemini-key"
        assert retrieved.outlook_configured is True
        assert retrieved.outlook_refresh_token == "refresh_token_abc"
        assert retrieved.extraction_prompt == "Custom prompt template"
        assert retrieved.onboarding_dismissed is True

    def test_update_settings(self, db_session):
        """Test updating settings."""
        repo = SqlAlchemySettingsRepository(db_session)

        settings1 = Settings.create()
        settings1.set_api_key("old-key")
        repo.save(settings1)

        settings2 = Settings.create()
        settings2.id = settings1.id
        settings2.set_api_key("new-key")
        settings2.default_export_path = "/path/to/exports"
        settings2.set_onboarding_dismissed(True)
        repo.save(settings2)

        retrieved = repo.get()
        assert retrieved is not None
        assert retrieved.gemini_api_key == "new-key"
        assert retrieved.default_export_path == "/path/to/exports"
        assert retrieved.onboarding_dismissed is True

    def test_get_empty_returns_none(self, db_session):
        """Test that get returns None when no settings exist."""
        repo = SqlAlchemySettingsRepository(db_session)

        result = repo.get()

        assert result is None

    def test_get_migrates_legacy_plaintext_outlook_token_to_keychain_reference(self, db_session):
        """Test legacy plaintext refresh token gets migrated to keychain reference on read."""
        legacy_model = SettingsModel(
            id=uuid4(),
            gemini_api_key="",
            outlook_configured=True,
            outlook_refresh_token="legacy-refresh-token",
            default_export_path="",
            extraction_prompt="",
            onboarding_dismissed=False,
        )
        db_session.add(legacy_model)
        db_session.commit()

        repo = SqlAlchemySettingsRepository(db_session)

        class FakeTokenVault:
            def __init__(self):
                self.saved: list[tuple[object, str]] = []

            def save_token(self, settings_id, refresh_token):
                self.saved.append((settings_id, refresh_token))
                return f"keychain://ai-bookkeeper/outlook-refresh-token/settings-{settings_id}"

            def load_token(self, _settings_id, stored_value):
                return stored_value

            def delete_token(self, _settings_id, _stored_value):
                return None

            def is_keychain_reference(self, stored_value):
                return stored_value.startswith("keychain://")

        fake_vault = FakeTokenVault()
        repo._token_vault = fake_vault

        retrieved = repo.get()
        assert retrieved is not None
        assert retrieved.outlook_refresh_token == "legacy-refresh-token"
        assert fake_vault.saved == [(legacy_model.id, "legacy-refresh-token")]

        stored = db_session.query(SettingsModel).first()
        assert stored is not None
        assert stored.outlook_refresh_token.startswith("keychain://ai-bookkeeper/outlook-refresh-token/")
    def test_get_keeps_legacy_plaintext_when_keychain_migration_fails(self, db_session):
        """Test plaintext token remains usable if migration to keychain fails."""
        legacy_model = SettingsModel(
            id=uuid4(),
            gemini_api_key="",
            outlook_configured=True,
            outlook_refresh_token="legacy-refresh-token",
            default_export_path="",
            extraction_prompt="",
            onboarding_dismissed=False,
        )
        db_session.add(legacy_model)
        db_session.commit()

        repo = SqlAlchemySettingsRepository(db_session)

        class FailingMigrationTokenVault:
            def save_token(self, _settings_id, _refresh_token):
                raise RuntimeError("Keychain unavailable")

            def load_token(self, _settings_id, stored_value):
                return stored_value

            def delete_token(self, _settings_id, _stored_value):
                return None

            def is_keychain_reference(self, stored_value):
                return stored_value.startswith("keychain://")

        repo._token_vault = FailingMigrationTokenVault()

        retrieved = repo.get()
        assert retrieved is not None
        assert retrieved.outlook_refresh_token == "legacy-refresh-token"

        stored = db_session.query(SettingsModel).first()
        assert stored is not None
        assert stored.outlook_refresh_token == "legacy-refresh-token"

    def test_disconnect_settings_clears_existing_keychain_reference(self, db_session):
        """Test Outlook disconnect clears stored reference and calls vault cleanup."""
        repo = SqlAlchemySettingsRepository(db_session)

        class FakeTokenVault:
            def __init__(self):
                self.deleted: list[tuple[object, str]] = []

            def save_token(self, settings_id, _refresh_token):
                return f"keychain://ai-bookkeeper/outlook-refresh-token/settings-{settings_id}"

            def load_token(self, _settings_id, stored_value):
                return stored_value

            def delete_token(self, settings_id, stored_value):
                self.deleted.append((settings_id, stored_value))

            def is_keychain_reference(self, stored_value):
                return stored_value.startswith("keychain://")

        fake_vault = FakeTokenVault()
        repo._token_vault = fake_vault

        connected = Settings.create()
        connected.set_outlook_configured(True, "refresh-token-value")
        repo.save(connected)

        disconnected = Settings.create()
        disconnected.id = connected.id
        disconnected.set_outlook_configured(False, "")
        repo.save(disconnected)

        stored = db_session.query(SettingsModel).first()
        assert stored is not None
        assert stored.outlook_configured is False
        assert stored.outlook_refresh_token == ""
        assert fake_vault.deleted == [
            (
                connected.id,
                f"keychain://ai-bookkeeper/outlook-refresh-token/settings-{connected.id}",
            )
        ]
