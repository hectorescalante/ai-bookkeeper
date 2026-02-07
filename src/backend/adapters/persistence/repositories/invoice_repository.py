"""SQLite repository for Invoice entities."""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from backend.adapters.persistence.mappers import (
    client_invoice_to_model,
    model_to_client_invoice,
    model_to_provider_invoice,
    provider_invoice_to_model,
)
from backend.adapters.persistence.models.invoice import ClientInvoiceModel, ProviderInvoiceModel
from backend.domain.entities.invoice import ClientInvoice, ProviderInvoice
from backend.ports.output.repositories import InvoiceFilters, InvoiceRepository


class SqlAlchemyInvoiceRepository(InvoiceRepository):
    """SQLite implementation of InvoiceRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save_client_invoice(self, invoice: ClientInvoice) -> None:
        """Save a client invoice (revenue)."""
        model = client_invoice_to_model(invoice)
        self.session.add(model)
        self.session.commit()

    def save_provider_invoice(self, invoice: ProviderInvoice) -> None:
        """Save a provider invoice (cost)."""
        model = provider_invoice_to_model(invoice)
        self.session.add(model)
        self.session.commit()

    def find_client_invoice(self, invoice_number: str, client_id: UUID) -> ClientInvoice | None:
        """Find client invoice by number and client ID."""
        model = (
            self.session.query(ClientInvoiceModel)
            .filter(
                ClientInvoiceModel.invoice_number == invoice_number,
                ClientInvoiceModel.client_id == client_id,
            )
            .first()
        )
        if model is None:
            return None
        return model_to_client_invoice(model)

    def find_provider_invoice(
        self, invoice_number: str, provider_id: UUID
    ) -> ProviderInvoice | None:
        """Find provider invoice by number and provider ID."""
        model = (
            self.session.query(ProviderInvoiceModel)
            .filter(
                ProviderInvoiceModel.invoice_number == invoice_number,
                ProviderInvoiceModel.provider_id == provider_id,
            )
            .first()
        )
        if model is None:
            return None
        return model_to_provider_invoice(model)

    def list_client_invoices(self, filters: InvoiceFilters | None = None) -> list[ClientInvoice]:
        """List client invoices with optional filtering."""
        query = self.session.query(ClientInvoiceModel)

        if filters:
            if filters.client_id:
                query = query.filter(ClientInvoiceModel.client_id == filters.client_id)
            if filters.booking_id:
                query = query.filter(ClientInvoiceModel.bl_reference == filters.booking_id)
            if filters.date_from:
                query = query.filter(
                    ClientInvoiceModel.invoice_date >= date.fromisoformat(filters.date_from)
                )
            if filters.date_to:
                query = query.filter(
                    ClientInvoiceModel.invoice_date <= date.fromisoformat(filters.date_to)
                )

        models = query.order_by(ClientInvoiceModel.invoice_date.desc()).all()
        return [model_to_client_invoice(model) for model in models]

    def list_provider_invoices(
        self, filters: InvoiceFilters | None = None
    ) -> list[ProviderInvoice]:
        """List provider invoices with optional filtering."""
        query = self.session.query(ProviderInvoiceModel)

        if filters:
            if filters.provider_id:
                query = query.filter(ProviderInvoiceModel.provider_id == filters.provider_id)
            if filters.booking_id:
                # Provider invoices can have multiple BL references (JSON array)
                # This requires JSON querying which is database-specific
                # For SQLite, we use the JSON_EXTRACT function
                query = query.filter(
                    ProviderInvoiceModel.bl_references.contains([filters.booking_id])
                )
            if filters.date_from:
                query = query.filter(
                    ProviderInvoiceModel.invoice_date >= date.fromisoformat(filters.date_from)
                )
            if filters.date_to:
                query = query.filter(
                    ProviderInvoiceModel.invoice_date <= date.fromisoformat(filters.date_to)
                )

        models = query.order_by(ProviderInvoiceModel.invoice_date.desc()).all()
        return [model_to_provider_invoice(model) for model in models]
