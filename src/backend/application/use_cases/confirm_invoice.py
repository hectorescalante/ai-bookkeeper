"""Use case to confirm reviewed extraction data and persist invoice entities."""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.application.dtos.invoice_dtos import (
    ConfirmInvoiceRequest,
    ConfirmInvoiceResponse,
    SaveChargeInput,
)
from backend.domain.entities.booking import Booking
from backend.domain.entities.invoice import ClientInvoice, ProviderInvoice
from backend.domain.entities.party import Client, Provider
from backend.domain.enums import ChargeCategory, ConfidenceLevel, DocumentType, ProviderType
from backend.domain.value_objects import (
    BookingCharge,
    ClientInfo,
    DocumentReference,
    ExtractionMetadata,
    FileHash,
    Money,
    Port,
)
from backend.ports.output.repositories import (
    BookingRepository,
    ClientRepository,
    DocumentRepository,
    InvoiceRepository,
    ProviderRepository,
)


class ConfirmInvoiceUseCase:
    """Persist reviewed invoice extraction into domain aggregates."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        booking_repo: BookingRepository,
        invoice_repo: InvoiceRepository,
        client_repo: ClientRepository,
        provider_repo: ProviderRepository,
    ) -> None:
        self.document_repo = document_repo
        self.booking_repo = booking_repo
        self.invoice_repo = invoice_repo
        self.client_repo = client_repo
        self.provider_repo = provider_repo

    def execute(self, request: ConfirmInvoiceRequest) -> ConfirmInvoiceResponse:
        """Confirm and save reviewed invoice data."""
        document = self.document_repo.find_by_id(request.document_id)
        if document is None:
            raise ValueError(f"Document not found: {request.document_id}")

        self._cleanup_existing_projection_for_document(document.id)

        try:
            document_type = DocumentType(request.document_type)
        except ValueError as exc:
            raise ValueError(f"Invalid document_type: {request.document_type}") from exc

        # Non-invoice documents can be closed without invoice persistence.
        if document_type == DocumentType.OTHER:
            document.mark_processed(DocumentType.OTHER)
            self.document_repo.update(document)
            return ConfirmInvoiceResponse(
                document_id=document.id,
                invoice_id=None,
                document_type=document_type.value,
                status=document.status.value,
                booking_ids=[],
            )

        if not request.invoice_number:
            raise ValueError("invoice_number is required")
        if not request.invoice_date:
            raise ValueError("invoice_date is required")
        if not request.charges:
            raise ValueError("At least one charge is required")

        invoice_date = date.fromisoformat(request.invoice_date)
        bl_references = self._extract_bl_references(request.bl_references)
        if not bl_references:
            bl_references = self._extract_bl_references_from_charges(request.charges)
        if not bl_references:
            raise ValueError("At least one BL reference is required")

        source_document = DocumentReference(
            document_id=document.id,
            filename=document.filename,
            file_hash=FileHash(
                algorithm=document.file_hash.algorithm,
                value=document.file_hash.value,
            ),
        )
        extraction_metadata = self._build_extraction_metadata(request)

        if document_type == DocumentType.CLIENT_INVOICE:
            invoice_id, booking_ids = self._persist_client_invoice(
                request=request,
                invoice_date=invoice_date,
                bl_references=bl_references,
                source_document=source_document,
                extraction_metadata=extraction_metadata,
            )
        else:
            invoice_id, booking_ids = self._persist_provider_invoice(
                request=request,
                invoice_date=invoice_date,
                bl_references=bl_references,
                source_document=source_document,
                extraction_metadata=extraction_metadata,
            )

        document.mark_processed(document_type=document_type, invoice_id=invoice_id)
        self.document_repo.update(document)

        return ConfirmInvoiceResponse(
            document_id=document.id,
            invoice_id=invoice_id,
            document_type=document_type.value,
            status=document.status.value,
            booking_ids=booking_ids,
        )

    def _persist_client_invoice(
        self,
        request: ConfirmInvoiceRequest,
        invoice_date: date,
        bl_references: list[str],
        source_document: DocumentReference,
        extraction_metadata: ExtractionMetadata,
    ) -> tuple[UUID, list[str]]:
        client_nif = (request.recipient_nif or "").strip()
        if not client_nif:
            raise ValueError("recipient_nif is required for CLIENT_INVOICE")

        client = self.client_repo.find_by_nif(client_nif)
        if client is None:
            client = Client.create(nif=client_nif, name=request.recipient_name)
            self.client_repo.save(client)

        primary_bl_reference = bl_references[0]
        existing = self.invoice_repo.find_client_invoice(
            invoice_number=request.invoice_number or "",
            client_id=client.id,
        )
        if existing is not None:
            raise ValueError("Client invoice already exists for invoice_number + client")

        charges_total = self._sum_charge_amounts(request.charges)
        tax_amount = self._to_money(request.totals.get("tax_amount", "0"))
        total_amount = self._to_money(request.totals.get("total")) if request.totals.get(
            "total"
        ) is not None else charges_total + tax_amount

        invoice = ClientInvoice.create(
            invoice_number=request.invoice_number or "",
            client_id=client.id,
            invoice_date=invoice_date,
            bl_reference=primary_bl_reference,
            total_amount=total_amount,
            tax_amount=tax_amount,
        )
        invoice.source_document = source_document
        invoice.extraction_metadata = extraction_metadata

        referenced_bookings: set[str] = set()
        for charge_input in request.charges:
            booking_id = (charge_input.bl_reference or primary_bl_reference).strip()
            referenced_bookings.add(booking_id)

            charge = BookingCharge(
                booking_id=booking_id,
                invoice_id=invoice.id,
                charge_category=self._parse_charge_category(charge_input.category),
                provider_type=None,
                container=charge_input.container,
                description=charge_input.description,
                amount=self._to_money(charge_input.amount),
            )
            invoice.add_charge(charge)

        for booking_id in sorted(referenced_bookings):
            booking = self.booking_repo.find_or_create(booking_id)
            booking.update_client(
                ClientInfo(
                    client_id=client.id,
                    name=client.name,
                    nif=client.nif,
                )
            )
            self._apply_shipping_details(booking, request)

            for charge in invoice.charges:
                if charge.booking_id == booking_id:
                    booking.add_revenue_charge(charge)
            self.booking_repo.save(booking)

        self.invoice_repo.save_client_invoice(invoice)
        return invoice.id, sorted(referenced_bookings)

    def _persist_provider_invoice(
        self,
        request: ConfirmInvoiceRequest,
        invoice_date: date,
        bl_references: list[str],
        source_document: DocumentReference,
        extraction_metadata: ExtractionMetadata,
    ) -> tuple[UUID, list[str]]:
        provider_nif = (request.issuer_nif or "").strip()
        if not provider_nif:
            raise ValueError("issuer_nif is required for PROVIDER_INVOICE")

        provider_type = self._parse_provider_type(request.provider_type)

        provider = self.provider_repo.find_by_nif(provider_nif)
        if provider is None:
            provider = Provider.create(
                nif=provider_nif,
                provider_type=provider_type,
                name=request.issuer_name,
            )
            self.provider_repo.save(provider)

        existing = self.invoice_repo.find_provider_invoice(
            invoice_number=request.invoice_number or "",
            provider_id=provider.id,
        )
        if existing is not None:
            raise ValueError("Provider invoice already exists for invoice_number + provider")

        charges_total = self._sum_charge_amounts(request.charges)
        tax_amount = self._to_money(request.totals.get("tax_amount", "0"))
        total_amount = self._to_money(request.totals.get("total")) if request.totals.get(
            "total"
        ) is not None else charges_total + tax_amount

        invoice = ProviderInvoice.create(
            invoice_number=request.invoice_number or "",
            provider_id=provider.id,
            provider_type=provider.provider_type,
            invoice_date=invoice_date,
            bl_references=bl_references,
            total_amount=total_amount,
            tax_amount=tax_amount,
        )
        invoice.source_document = source_document
        invoice.extraction_metadata = extraction_metadata

        referenced_bookings: set[str] = set()
        default_booking_id = bl_references[0]

        for charge_input in request.charges:
            booking_id = (charge_input.bl_reference or default_booking_id).strip()
            referenced_bookings.add(booking_id)

            charge = BookingCharge(
                booking_id=booking_id,
                invoice_id=invoice.id,
                charge_category=self._parse_charge_category(charge_input.category),
                provider_type=provider.provider_type,
                container=charge_input.container,
                description=charge_input.description,
                amount=self._to_money(charge_input.amount),
            )
            invoice.add_charge(charge)

        for booking_id in sorted(referenced_bookings):
            booking = self.booking_repo.find_or_create(booking_id)
            self._apply_shipping_details(booking, request)

            for charge in invoice.charges:
                if charge.booking_id == booking_id:
                    booking.add_cost_charge(charge)
            self.booking_repo.save(booking)

        self.invoice_repo.save_provider_invoice(invoice)
        return invoice.id, sorted(referenced_bookings)

    def _extract_bl_references(self, references: list[str | dict[str, Any]]) -> list[str]:
        result: list[str] = []
        for item in references:
            if isinstance(item, str):
                value = item.strip()
                if value:
                    result.append(value)
            elif isinstance(item, dict):
                value = str(item.get("bl_number", "")).strip()
                if value:
                    result.append(value)
        return list(dict.fromkeys(result))

    def _extract_bl_references_from_charges(self, charges: list[SaveChargeInput]) -> list[str]:
        refs = []
        for charge in charges:
            if charge.bl_reference:
                value = charge.bl_reference.strip()
                if value:
                    refs.append(value)
        return list(dict.fromkeys(refs))

    def _parse_charge_category(self, value: str) -> ChargeCategory:
        try:
            return ChargeCategory(value.upper())
        except ValueError:
            return ChargeCategory.OTHER

    def _parse_provider_type(self, value: str | None) -> ProviderType:
        if not value:
            return ProviderType.OTHER
        try:
            return ProviderType(value.upper())
        except ValueError:
            return ProviderType.OTHER

    def _to_money(self, value: object) -> Money:
        if value is None or value == "":
            return Money.zero()
        return Money(Decimal(str(value)))

    def _sum_charge_amounts(self, charges: list[SaveChargeInput]) -> Money:
        return sum((self._to_money(c.amount) for c in charges), Money.zero())

    def _build_extraction_metadata(self, request: ConfirmInvoiceRequest) -> ExtractionMetadata:
        confidence = self._parse_confidence(request.overall_confidence)
        return ExtractionMetadata(
            ai_model=request.ai_model,
            overall_confidence=confidence,
            raw_json=request.raw_json,
            manually_edited_fields=tuple(request.manually_edited_fields),
        )

    def _parse_confidence(self, value: str) -> ConfidenceLevel:
        try:
            return ConfidenceLevel(value.upper())
        except ValueError:
            return ConfidenceLevel.LOW

    def _apply_shipping_details(self, booking: Booking, request: ConfirmInvoiceRequest) -> None:
        shipping = request.shipping_details or {}

        pol_data = shipping.get("pol")
        pod_data = shipping.get("pod")

        pol = None
        pod = None
        if isinstance(pol_data, dict) and pol_data.get("code"):
            pol = Port(code=str(pol_data.get("code")), name=str(pol_data.get("name", "")))
        if isinstance(pod_data, dict) and pod_data.get("code"):
            pod = Port(code=str(pod_data.get("code")), name=str(pod_data.get("name", "")))
        if pol is not None or pod is not None:
            booking.update_ports(pol=pol, pod=pod)

        vessel = shipping.get("vessel")
        if vessel:
            booking.vessel = str(vessel)

        containers = shipping.get("containers")
        if isinstance(containers, list):
            booking.containers = [str(container) for container in containers if container]

    def _cleanup_existing_projection_for_document(self, document_id: UUID) -> None:
        """Remove previously persisted projection for a source document."""
        replaced_invoice_ids = self.invoice_repo.delete_by_source_document(document_id)
        if not replaced_invoice_ids:
            return

        bookings = self.booking_repo.list_all()
        for booking in bookings:
            booking_changed = False
            for invoice_id in replaced_invoice_ids:
                booking_changed = (
                    booking.remove_charges_for_invoice(invoice_id) or booking_changed
                )
            if booking_changed:
                self.booking_repo.update(booking)
