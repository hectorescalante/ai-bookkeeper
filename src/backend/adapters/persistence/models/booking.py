"""SQLAlchemy model for Booking entity."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from backend.adapters.persistence.database import Base


class BookingModel(Base):
    """ORM model for Booking entity (primary aggregate)."""

    __tablename__ = "bookings"
    __table_args__ = (Index("ix_bookings_status", "status"), Index("ix_bookings_uuid", "uuid"))

    # BL reference is the primary business identifier
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Internal UUID for referential integrity
    uuid: Mapped[UUID] = mapped_column(unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # Client reference (nullable until first invoice)
    client_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), index=True
    )

    # Port of Loading (nullable)
    pol_code: Mapped[str | None] = mapped_column(String(10))
    pol_name: Mapped[str | None] = mapped_column(String(255))

    # Port of Discharge (nullable)
    pod_code: Mapped[str | None] = mapped_column(String(10))
    pod_name: Mapped[str | None] = mapped_column(String(255))

    # Vessel (nullable)
    vessel: Mapped[str | None] = mapped_column(String(255))

    # Containers stored as JSON array of strings
    containers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('PENDING', 'COMPLETE')", name="ck_booking_status"),
        nullable=False,
        default="PENDING",
    )

    # Charges stored as JSON arrays
    revenue_charges: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    cost_charges: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
