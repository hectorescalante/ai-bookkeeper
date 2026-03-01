"""SQLAlchemy models for configuration entities (singletons)."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.adapters.persistence.database import Base


class CompanyModel(Base):
    """ORM model for Company entity (singleton)."""

    __tablename__ = "company"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    nif: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    address: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    contact_info: Mapped[str] = mapped_column(String(500), nullable=False, default="")
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
    gemini_api_key: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    outlook_configured: Mapped[bool] = mapped_column(nullable=False, default=False)
    outlook_refresh_token: Mapped[str] = mapped_column(Text, nullable=False, default="")
    default_export_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    extraction_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    onboarding_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class OutlookOAuthStateModel(Base):
    """ORM model storing pending Outlook OAuth sessions."""

    __tablename__ = "outlook_oauth_states"

    state: Mapped[str] = mapped_column(String(255), primary_key=True)
    flow_payload: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
