"""SQLAlchemy models for Client and Provider entities."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.adapters.persistence.database import Base


class ClientModel(Base):
    """ORM model for Client entity."""

    __tablename__ = "clients"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    nif: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class ProviderModel(Base):
    """ORM model for Provider entity."""

    __tablename__ = "providers"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    nif: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "provider_type IN ('SHIPPING', 'CARRIER', 'INSPECTION', 'OTHER')",
            name="ck_provider_type",
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False)
