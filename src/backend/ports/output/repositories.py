"""Output ports: Repository interfaces for persistence.

These are abstract interfaces that define how the application interacts with
persistence, following the dependency inversion principle.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from backend.domain.entities.booking import Booking
from backend.domain.entities.configuration import Agent, Company, Settings
from backend.domain.entities.document import Document
from backend.domain.entities.invoice import ClientInvoice, ProviderInvoice
from backend.domain.entities.party import Client, Provider
from backend.domain.enums import BookingStatus, ProcessingStatus, ProviderType
from backend.domain.value_objects import FileHash

# --- Filter and Sort Data Classes ---


@dataclass
class BookingFilters:
    """Filters for booking queries."""

    client_id: UUID | None = None
    status: BookingStatus | None = None
    date_from: str | None = None  # ISO format date
    date_to: str | None = None  # ISO format date


@dataclass
class BookingSort:
    """Sort options for booking queries."""

    field: str = "created_at"  # created_at, margin, commission
    descending: bool = True


@dataclass
class InvoiceFilters:
    """Filters for invoice queries."""

    client_id: UUID | None = None
    provider_id: UUID | None = None
    booking_id: str | None = None
    date_from: str | None = None  # ISO format date
    date_to: str | None = None  # ISO format date


# --- Repository Interfaces ---


class BookingRepository(ABC):
    """Repository for Booking aggregate persistence."""

    @abstractmethod
    def save(self, booking: Booking) -> None:
        """Save a new booking or update existing one."""
        pass

    @abstractmethod
    def find_by_id(self, bl_reference: str) -> Booking | None:
        """Find booking by BL reference."""
        pass

    @abstractmethod
    def find_or_create(self, bl_reference: str) -> Booking:
        """Find booking by ID, or create if it doesn't exist."""
        pass

    @abstractmethod
    def list_all(
        self, filters: BookingFilters | None = None, sort: BookingSort | None = None
    ) -> list[Booking]:
        """List all bookings with optional filtering and sorting."""
        pass

    @abstractmethod
    def update(self, booking: Booking) -> None:
        """Update an existing booking."""
        pass


class InvoiceRepository(ABC):
    """Repository for invoice persistence (both client and provider)."""

    @abstractmethod
    def save_client_invoice(self, invoice: ClientInvoice) -> None:
        """Save a client invoice (revenue)."""
        pass

    @abstractmethod
    def save_provider_invoice(self, invoice: ProviderInvoice) -> None:
        """Save a provider invoice (cost)."""
        pass

    @abstractmethod
    def find_client_invoice_by_id(self, invoice_id: UUID) -> ClientInvoice | None:
        """Find client invoice by invoice ID."""
        pass

    @abstractmethod
    def find_provider_invoice_by_id(self, invoice_id: UUID) -> ProviderInvoice | None:
        """Find provider invoice by invoice ID."""
        pass

    @abstractmethod
    def find_client_invoice(self, invoice_number: str, client_id: UUID) -> ClientInvoice | None:
        """Find client invoice by number and client ID."""
        pass

    @abstractmethod
    def find_provider_invoice(
        self, invoice_number: str, provider_id: UUID
    ) -> ProviderInvoice | None:
        """Find provider invoice by number and provider ID."""
        pass

    @abstractmethod
    def list_client_invoices(self, filters: InvoiceFilters | None = None) -> list[ClientInvoice]:
        """List client invoices with optional filtering."""
        pass

    @abstractmethod
    def list_provider_invoices(
        self, filters: InvoiceFilters | None = None
    ) -> list[ProviderInvoice]:
        """List provider invoices with optional filtering."""
        pass

    @abstractmethod
    def delete_by_source_document(self, document_id: UUID) -> list[UUID]:
        """Delete invoices linked to a source document and return removed invoice IDs."""
        pass


class DocumentRepository(ABC):
    """Repository for document persistence."""

    @abstractmethod
    def save(self, document: Document) -> None:
        """Save a new document."""
        pass

    @abstractmethod
    def find_by_id(self, document_id: UUID) -> Document | None:
        """Find document by ID."""
        pass

    @abstractmethod
    def find_by_file_hash(self, file_hash: FileHash) -> Document | None:
        """Find document by file hash (for duplicate detection)."""
        pass

    @abstractmethod
    def list_by_status(self, status: ProcessingStatus) -> list[Document]:
        """List documents by processing status."""
        pass

    @abstractmethod
    def find_stuck_processing(self) -> list[Document]:
        """Find documents stuck in PROCESSING status (crash recovery)."""
        pass

    @abstractmethod
    def update(self, document: Document) -> None:
        """Update an existing document."""
        pass


class ClientRepository(ABC):
    """Repository for Client entity persistence."""

    @abstractmethod
    def save(self, client: Client) -> None:
        """Save a new client."""
        pass

    @abstractmethod
    def find_by_id(self, client_id: UUID) -> Client | None:
        """Find client by ID."""
        pass

    @abstractmethod
    def find_by_nif(self, nif: str) -> Client | None:
        """Find client by NIF (tax ID)."""
        pass

    @abstractmethod
    def list_all(self) -> list[Client]:
        """List all clients."""
        pass


class ProviderRepository(ABC):
    """Repository for Provider entity persistence."""

    @abstractmethod
    def save(self, provider: Provider) -> None:
        """Save a new provider."""
        pass

    @abstractmethod
    def find_by_id(self, provider_id: UUID) -> Provider | None:
        """Find provider by ID."""
        pass

    @abstractmethod
    def find_by_nif(self, nif: str) -> Provider | None:
        """Find provider by NIF (tax ID)."""
        pass

    @abstractmethod
    def list_all(self, provider_type: ProviderType | None = None) -> list[Provider]:
        """List all providers, optionally filtered by type."""
        pass


class CompanyRepository(ABC):
    """Repository for Company singleton entity."""

    @abstractmethod
    def save(self, company: Company) -> None:
        """Save or update company configuration."""
        pass

    @abstractmethod
    def get(self) -> Company | None:
        """Get company configuration (singleton)."""
        pass


class AgentRepository(ABC):
    """Repository for Agent singleton entity."""

    @abstractmethod
    def save(self, agent: Agent) -> None:
        """Save or update agent profile."""
        pass

    @abstractmethod
    def get(self) -> Agent | None:
        """Get agent profile (singleton)."""
        pass


class SettingsRepository(ABC):
    """Repository for Settings singleton entity."""

    @abstractmethod
    def save(self, settings: Settings) -> None:
        """Save or update application settings."""
        pass

    @abstractmethod
    def get(self) -> Settings | None:
        """Get application settings (singleton)."""
        pass
