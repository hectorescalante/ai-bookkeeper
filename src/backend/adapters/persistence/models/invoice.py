"""SQLAlchemy models for invoice entities."""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from backend.adapters.persistence.database import Base


class ClientInvoiceModel(Base):
    """ORM model for ClientInvoice entity (revenue)."""

    __tablename__ = "client_invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "client_id", name="uq_client_invoice_number"),
        Index("ix_client_invoices_bl_reference", "bl_reference"),
        Index("ix_client_invoices_date", "invoice_date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    invoice_date: Mapped[date] = mapped_column(nullable=False)
    bl_reference: Mapped[str] = mapped_column(
        ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False
    )

    # Money amounts
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_currency: Mapped[str] = mapped_column(
        String(3),
        CheckConstraint("total_currency = 'EUR'", name="ck_client_invoice_currency"),
        nullable=False,
        default="EUR",
    )
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_currency: Mapped[str] = mapped_column(
        String(3),
        CheckConstraint("tax_currency = 'EUR'", name="ck_client_invoice_tax_currency"),
        nullable=False,
        default="EUR",
    )

    # Charges stored as JSON array
    charges: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Source document reference
    source_document_id: Mapped[UUID | None]
    source_document_filename: Mapped[str | None] = mapped_column(String(500))
    source_document_hash_algo: Mapped[str | None] = mapped_column(String(20))
    source_document_hash_value: Mapped[str | None] = mapped_column(String(128))

    # Extraction metadata stored as JSON
    extraction_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class ProviderInvoiceModel(Base):
    """ORM model for ProviderInvoice entity (cost)."""

    __tablename__ = "provider_invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "provider_id", name="uq_provider_invoice_number"),
        Index("ix_provider_invoices_date", "invoice_date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "provider_type IN ('SHIPPING', 'CARRIER', 'INSPECTION', 'OTHER')",
            name="ck_provider_invoice_type",
        ),
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(nullable=False)

    # BL references (can be multiple for multi-booking invoices)
    bl_references: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    # Money amounts
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_currency: Mapped[str] = mapped_column(
        String(3),
        CheckConstraint("total_currency = 'EUR'", name="ck_provider_invoice_currency"),
        nullable=False,
        default="EUR",
    )
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_currency: Mapped[str] = mapped_column(
        String(3),
        CheckConstraint("tax_currency = 'EUR'", name="ck_provider_invoice_tax_currency"),
        nullable=False,
        default="EUR",
    )

    # Charges stored as JSON array
    charges: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Source document reference
    source_document_id: Mapped[UUID | None]
    source_document_filename: Mapped[str | None] = mapped_column(String(500))
    source_document_hash_algo: Mapped[str | None] = mapped_column(String(20))
    source_document_hash_value: Mapped[str | None] = mapped_column(String(128))

    # Extraction metadata stored as JSON
    extraction_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)
