"""SQLAlchemy models for configuration entities (singletons)."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.adapters.persistence.database import Base


class CompanyModel(Base):
    """ORM model for Company entity (singleton)."""

    __tablename__ = "company"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    nif: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    agent_commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0.50")
    )


class AgentModel(Base):
    """ORM model for Agent entity (singleton)."""

    __tablename__ = "agent"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")


class SettingsModel(Base):
    """ORM model for Settings entity (singleton)."""

    __tablename__ = "settings"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    anthropic_api_key: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    outlook_configured: Mapped[bool] = mapped_column(nullable=False, default=False)
    outlook_refresh_token: Mapped[str] = mapped_column(Text, nullable=False, default="")
    default_export_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    extraction_prompt: Mapped[str] = mapped_column(Text, nullable=False)
