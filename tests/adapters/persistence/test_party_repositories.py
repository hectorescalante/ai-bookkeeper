"""Integration tests for Client and Provider repositories."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from backend.adapters.persistence.repositories import (
    SqlAlchemyClientRepository,
    SqlAlchemyProviderRepository,
)
from backend.domain.entities.party import Client, Provider
from backend.domain.enums import ProviderType


class TestClientRepository:
    """Test suite for SqlAlchemyClientRepository."""

    def test_save_and_retrieve_client(self, db_session):
        """Test saving and retrieving a client."""
        repo = SqlAlchemyClientRepository(db_session)

        # Create and save client
        client = Client.create(nif="B12345678", name="Test Client SA")
        repo.save(client)

        # Retrieve
        retrieved = repo.find_by_id(client.id)

        assert retrieved is not None
        assert retrieved.id == client.id
        assert retrieved.name == "Test Client SA"
        assert retrieved.nif == "B12345678"

    def test_find_by_nif(self, db_session):
        """Test finding client by NIF."""
        repo = SqlAlchemyClientRepository(db_session)

        # Create client
        client = Client.create(nif="B12345678", name="Test Client")
        repo.save(client)

        # Find by NIF (with different formatting)
        retrieved = repo.find_by_nif("B-12345678")

        assert retrieved is not None
        assert retrieved.nif == "B12345678"

    def test_find_by_nif_not_found(self, db_session):
        """Test finding non-existent client returns None."""
        repo = SqlAlchemyClientRepository(db_session)

        result = repo.find_by_nif("B99999999")

        assert result is None

    def test_prevent_duplicate_nif(self, db_session):
        """Test that duplicate NIF raises error."""
        repo = SqlAlchemyClientRepository(db_session)

        # Create first client
        client1 = Client.create(nif="B12345678", name="Client 1")
        repo.save(client1)

        # Try to create second client with same NIF
        client2 = Client.create(nif="B12345678", name="Client 2")

        with pytest.raises(IntegrityError):
            repo.save(client2)

    def test_list_all_clients(self, db_session):
        """Test listing all clients."""
        repo = SqlAlchemyClientRepository(db_session)

        # Create multiple clients
        client1 = Client.create(nif="B11111111", name="Alpha Client")
        client2 = Client.create(nif="B22222222", name="Beta Client")
        client3 = Client.create(nif="B33333333", name="Gamma Client")

        repo.save(client1)
        repo.save(client2)
        repo.save(client3)

        # List all
        clients = repo.list_all()

        assert len(clients) == 3
        # Should be sorted by name
        assert clients[0].name == "Alpha Client"
        assert clients[1].name == "Beta Client"
        assert clients[2].name == "Gamma Client"


class TestProviderRepository:
    """Test suite for SqlAlchemyProviderRepository."""

    def test_save_and_retrieve_provider(self, db_session):
        """Test saving and retrieving a provider."""
        repo = SqlAlchemyProviderRepository(db_session)

        # Create and save provider
        provider = Provider.create(
            nif="B87654321", provider_type=ProviderType.SHIPPING, name="Test Shipping"
        )
        repo.save(provider)

        # Retrieve
        retrieved = repo.find_by_id(provider.id)

        assert retrieved is not None
        assert retrieved.id == provider.id
        assert retrieved.name == "Test Shipping"
        assert retrieved.nif == "B87654321"
        assert retrieved.provider_type == ProviderType.SHIPPING

    def test_find_by_nif(self, db_session):
        """Test finding provider by NIF."""
        repo = SqlAlchemyProviderRepository(db_session)

        # Create provider
        provider = Provider.create(nif="B87654321", name="Test Provider")
        repo.save(provider)

        # Find by NIF (with formatting)
        retrieved = repo.find_by_nif("B-87.654.321")

        assert retrieved is not None
        assert retrieved.nif == "B87654321"

    def test_prevent_duplicate_nif(self, db_session):
        """Test that duplicate NIF raises error."""
        repo = SqlAlchemyProviderRepository(db_session)

        # Create first provider
        provider1 = Provider.create(nif="B87654321", name="Provider 1")
        repo.save(provider1)

        # Try second with same NIF
        provider2 = Provider.create(nif="B87654321", name="Provider 2")

        with pytest.raises(IntegrityError):
            repo.save(provider2)

    def test_list_all_providers(self, db_session):
        """Test listing all providers."""
        repo = SqlAlchemyProviderRepository(db_session)

        # Create multiple providers
        p1 = Provider.create(nif="B11111111", provider_type=ProviderType.SHIPPING, name="Alpha")
        p2 = Provider.create(nif="B22222222", provider_type=ProviderType.CARRIER, name="Beta")
        p3 = Provider.create(nif="B33333333", provider_type=ProviderType.INSPECTION, name="Gamma")

        repo.save(p1)
        repo.save(p2)
        repo.save(p3)

        # List all
        providers = repo.list_all()

        assert len(providers) == 3

    def test_list_providers_filtered_by_type(self, db_session):
        """Test filtering providers by type."""
        repo = SqlAlchemyProviderRepository(db_session)

        # Create providers of different types
        p1 = Provider.create(nif="B11111111", provider_type=ProviderType.SHIPPING)
        p2 = Provider.create(nif="B22222222", provider_type=ProviderType.CARRIER)
        p3 = Provider.create(nif="B33333333", provider_type=ProviderType.SHIPPING)

        repo.save(p1)
        repo.save(p2)
        repo.save(p3)

        # Filter by SHIPPING
        shipping = repo.list_all(provider_type=ProviderType.SHIPPING)

        assert len(shipping) == 2
        assert all(p.provider_type == ProviderType.SHIPPING for p in shipping)
