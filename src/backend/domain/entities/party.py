"""Client and Provider entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from backend.domain.enums import ProviderType


def normalize_nif(nif: str) -> str:
    """Normalize NIF by removing spaces, dashes, and converting to uppercase."""
    return nif.replace(" ", "").replace("-", "").replace(".", "").upper()


@dataclass
class Client:
    """A client who receives invoices from the company.

    Clients are auto-created when processing client invoices.
    """

    id: UUID
    name: str
    nif: str  # Tax ID, unique identifier
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(cls, nif: str, name: str | None = None) -> "Client":
        """Create a new client.

        Args:
            nif: Tax ID (required, must be non-empty after normalization)
            name: Client name (optional, defaults to "Unknown Client")

        Raises:
            ValueError: If NIF is empty after normalization
        """
        normalized_nif = normalize_nif(nif)
        if not normalized_nif:
            raise ValueError("Client NIF cannot be empty")

        return cls(
            id=uuid4(),
            name=name or "Unknown Client",
            nif=normalized_nif,
        )

    def update_name(self, name: str) -> None:
        """Update client name."""
        self.name = name


@dataclass
class Provider:
    """A provider/vendor who sends invoices to the company.

    Providers are auto-created when processing provider invoices.
    """

    id: UUID
    name: str
    nif: str  # Tax ID, unique identifier
    provider_type: ProviderType
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        nif: str,
        provider_type: ProviderType = ProviderType.OTHER,
        name: str | None = None,
    ) -> "Provider":
        """Create a new provider.

        Args:
            nif: Tax ID (required, must be non-empty after normalization)
            provider_type: Type of provider (defaults to OTHER)
            name: Provider name (optional, defaults to "Unknown Provider")

        Raises:
            ValueError: If NIF is empty after normalization
        """
        normalized_nif = normalize_nif(nif)
        if not normalized_nif:
            raise ValueError("Provider NIF cannot be empty")

        return cls(
            id=uuid4(),
            name=name or "Unknown Provider",
            nif=normalized_nif,
            provider_type=provider_type,
        )

    def update_name(self, name: str) -> None:
        """Update provider name."""
        self.name = name

    def update_type(self, provider_type: ProviderType) -> None:
        """Update provider type.

        Note: Changes do NOT affect historical charges.
        """
        self.provider_type = provider_type
