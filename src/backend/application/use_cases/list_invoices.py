"""Use case for listing and searching persisted invoices."""

from datetime import date

from backend.application.dtos import InvoiceListItem, ListInvoicesRequest
from backend.ports.output.repositories import (
    ClientRepository,
    InvoiceFilters,
    InvoiceRepository,
    ProviderRepository,
)


class ListInvoicesUseCase:
    """List invoices with optional search filters."""

    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        client_repo: ClientRepository,
        provider_repo: ProviderRepository,
    ) -> None:
        self.invoice_repo = invoice_repo
        self.client_repo = client_repo
        self.provider_repo = provider_repo

    def execute(self, request: ListInvoicesRequest) -> list[InvoiceListItem]:
        """Execute invoice search over client and provider invoices."""
        date_from = self._parse_date(request.date_from, "date_from")
        date_to = self._parse_date(request.date_to, "date_to")
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from cannot be greater than date_to")

        invoice_type = self._normalize_invoice_type(request.invoice_type)
        invoice_number_filter = (request.invoice_number or "").strip().lower()
        party_filter = (request.party or "").strip().lower()

        repo_filters = InvoiceFilters(
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
        )

        items: list[InvoiceListItem] = []

        if invoice_type in (None, "CLIENT_INVOICE"):
            for client_invoice in self.invoice_repo.list_client_invoices(repo_filters):
                if (
                    invoice_number_filter
                    and invoice_number_filter not in client_invoice.invoice_number.lower()
                ):
                    continue
                client = self.client_repo.find_by_id(client_invoice.client_id)
                party_name = client.name if client else None
                if party_filter and party_filter not in (party_name or "").lower():
                    continue
                items.append(
                    InvoiceListItem(
                        id=client_invoice.id,
                        invoice_type="CLIENT_INVOICE",
                        invoice_number=client_invoice.invoice_number,
                        invoice_date=client_invoice.invoice_date,
                        party_name=party_name,
                        booking_references=[client_invoice.bl_reference],
                        total_amount=client_invoice.total_amount.amount,
                    )
                )

        if invoice_type in (None, "PROVIDER_INVOICE"):
            for provider_invoice in self.invoice_repo.list_provider_invoices(repo_filters):
                if (
                    invoice_number_filter
                    and invoice_number_filter not in provider_invoice.invoice_number.lower()
                ):
                    continue
                provider = self.provider_repo.find_by_id(provider_invoice.provider_id)
                party_name = provider.name if provider else None
                if party_filter and party_filter not in (party_name or "").lower():
                    continue
                items.append(
                    InvoiceListItem(
                        id=provider_invoice.id,
                        invoice_type="PROVIDER_INVOICE",
                        invoice_number=provider_invoice.invoice_number,
                        invoice_date=provider_invoice.invoice_date,
                        party_name=party_name,
                        booking_references=list(provider_invoice.bl_references),
                        total_amount=provider_invoice.total_amount.amount,
                    )
                )

        items.sort(key=lambda item: item.invoice_date, reverse=True)
        return items[: request.limit]

    @staticmethod
    def _parse_date(value: str | None, field_name: str) -> date | None:
        if value is None or not value.strip():
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Invalid {field_name}: {value}") from exc

    @staticmethod
    def _normalize_invoice_type(value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip().upper()
        if normalized not in {"CLIENT_INVOICE", "PROVIDER_INVOICE"}:
            raise ValueError(f"Invalid invoice_type: {value}")
        return normalized
