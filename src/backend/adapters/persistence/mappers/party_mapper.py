"""Mappers for Client and Provider entities."""

from backend.adapters.persistence.models.party import ClientModel, ProviderModel
from backend.domain.entities.party import Client, Provider
from backend.domain.enums import ProviderType


def client_to_model(client: Client) -> ClientModel:
    """Convert Client entity to ClientModel ORM."""
    return ClientModel(
        id=client.id,
        name=client.name,
        nif=client.nif,
        created_at=client.created_at,
    )


def model_to_client(model: ClientModel) -> Client:
    """Convert ClientModel ORM to Client entity."""
    return Client(
        id=model.id,
        name=model.name,
        nif=model.nif,
        created_at=model.created_at,
    )


def provider_to_model(provider: Provider) -> ProviderModel:
    """Convert Provider entity to ProviderModel ORM."""
    return ProviderModel(
        id=provider.id,
        name=provider.name,
        nif=provider.nif,
        provider_type=provider.provider_type.value,
        created_at=provider.created_at,
    )


def model_to_provider(model: ProviderModel) -> Provider:
    """Convert ProviderModel ORM to Provider entity."""
    return Provider(
        id=model.id,
        name=model.name,
        nif=model.nif,
        provider_type=ProviderType(model.provider_type),
        created_at=model.created_at,
    )
