"""Identifier and info value objects."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ClientInfo:
    """Denormalized client information stored in bookings.

    This is a snapshot of client data at the time of booking creation,
    allowing bookings to be displayed without joining to the client table.
    """

    client_id: UUID
    name: str
    nif: str


@dataclass(frozen=True, slots=True)
class Port:
    """A shipping port with code and name."""

    code: str  # e.g., "ESVAL" for Valencia
    name: str  # e.g., "Valencia, Spain"

    def __str__(self) -> str:
        """Format as string."""
        return f"{self.code} ({self.name})" if self.name else self.code
