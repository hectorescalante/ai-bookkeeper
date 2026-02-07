"""Domain entities - aggregate roots and entities."""

from backend.domain.entities.booking import Booking
from backend.domain.entities.configuration import Agent, Company, Settings
from backend.domain.entities.document import Document
from backend.domain.entities.invoice import ClientInvoice, ProviderInvoice
from backend.domain.entities.party import Client, Provider, normalize_nif

__all__ = [
    "Agent",
    "Booking",
    "Client",
    "ClientInvoice",
    "Company",
    "Document",
    "Provider",
    "ProviderInvoice",
    "Settings",
    "normalize_nif",
]
