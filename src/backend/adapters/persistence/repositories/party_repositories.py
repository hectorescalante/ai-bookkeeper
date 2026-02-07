"""SQLite repositories for Client and Provider entities."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.adapters.persistence.mappers import (
    client_to_model,
    model_to_client,
    model_to_provider,
    provider_to_model,
)
from backend.adapters.persistence.models.party import ClientModel, ProviderModel
from backend.domain.entities.party import Client, Provider, normalize_nif
from backend.domain.enums import ProviderType
from backend.ports.output.repositories import ClientRepository, ProviderRepository


class SqlAlchemyClientRepository(ClientRepository):
    """SQLite implementation of ClientRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, client: Client) -> None:
        """Save a new client."""
        model = client_to_model(client)
        self.session.add(model)
        self.session.commit()

    def find_by_id(self, client_id: UUID) -> Client | None:
        """Find client by ID."""
        model = self.session.query(ClientModel).filter(ClientModel.id == client_id).first()
        if model is None:
            return None
        return model_to_client(model)

    def find_by_nif(self, nif: str) -> Client | None:
        """Find client by NIF (tax ID)."""
        normalized_nif = normalize_nif(nif)
        model = self.session.query(ClientModel).filter(ClientModel.nif == normalized_nif).first()
        if model is None:
            return None
        return model_to_client(model)

    def list_all(self) -> list[Client]:
        """List all clients."""
        models = self.session.query(ClientModel).order_by(ClientModel.name).all()
        return [model_to_client(model) for model in models]


class SqlAlchemyProviderRepository(ProviderRepository):
    """SQLite implementation of ProviderRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, provider: Provider) -> None:
        """Save a new provider."""
        model = provider_to_model(provider)
        self.session.add(model)
        self.session.commit()

    def find_by_id(self, provider_id: UUID) -> Provider | None:
        """Find provider by ID."""
        model = self.session.query(ProviderModel).filter(ProviderModel.id == provider_id).first()
        if model is None:
            return None
        return model_to_provider(model)

    def find_by_nif(self, nif: str) -> Provider | None:
        """Find provider by NIF (tax ID)."""
        normalized_nif = normalize_nif(nif)
        model = (
            self.session.query(ProviderModel).filter(ProviderModel.nif == normalized_nif).first()
        )
        if model is None:
            return None
        return model_to_provider(model)

    def list_all(self, provider_type: ProviderType | None = None) -> list[Provider]:
        """List all providers, optionally filtered by type."""
        query = self.session.query(ProviderModel)

        if provider_type:
            query = query.filter(ProviderModel.provider_type == provider_type.value)

        models = query.order_by(ProviderModel.name).all()
        return [model_to_provider(model) for model in models]
