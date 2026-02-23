"""Integration tests for bookings API endpoints."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.domain.entities.booking import Booking
from backend.domain.enums import ChargeCategory, ProviderType
from backend.domain.value_objects import BookingCharge, ClientInfo, Money


@pytest.fixture
def _sample_bookings(db_session):
    """Create sample bookings for testing."""
    from datetime import datetime
    from uuid import uuid4

    from backend.adapters.persistence.models.party import ClientModel
    from backend.adapters.persistence.repositories.booking_repository import (
        SqlAlchemyBookingRepository,
    )

    client_id1 = uuid4()
    client_id2 = uuid4()

    client1 = ClientModel(
        id=client_id1, name="Client A", nif="B12345678", created_at=datetime.now()
    )
    client2 = ClientModel(
        id=client_id2, name="Client B", nif="B87654321", created_at=datetime.now()
    )

    db_session.add(client1)
    db_session.add(client2)
    db_session.commit()

    # Now create bookings
    repo = SqlAlchemyBookingRepository(db_session)

    # Create booking with charges
    booking1 = Booking.create("BL-2024-001")
    booking1.update_client(ClientInfo(client_id1, "Client A", "B12345678"))
    invoice_id1 = uuid4()
    invoice_id2 = uuid4()
    invoice_id3 = uuid4()
    booking1.add_revenue_charge(
        BookingCharge(
            booking_id="BL-2024-001",
            invoice_id=invoice_id1,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,  # Revenue charge
            container="CONT001",
            description="Ocean Freight",
            amount=Money(Decimal("1000.00")),
        )
    )
    booking1.add_cost_charge(
        BookingCharge(
            booking_id="BL-2024-001",
            invoice_id=invoice_id2,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.CARRIER,
            container="CONT001",
            description="Carrier Cost",
            amount=Money(Decimal("600.00")),
        )
    )
    repo.save(booking1)

    # Create another booking
    booking2 = Booking.create("BL-2024-002")
    booking2.update_client(ClientInfo(client_id2, "Client B", "B87654321"))
    booking2.add_revenue_charge(
        BookingCharge(
            booking_id="BL-2024-002",
            invoice_id=invoice_id3,
            charge_category=ChargeCategory.HANDLING,
            provider_type=None,  # Revenue charge
            container=None,
            description="Handling Fee",
            amount=Money(Decimal("500.00")),
        )
    )
    repo.save(booking2)

    # Commit to ensure data is persisted
    db_session.commit()
    return [booking1, booking2]


def test_list_all_bookings(client: TestClient, _sample_bookings) -> None:
    """Test GET /api/bookings."""
    response = client.get("/api/bookings")

    assert response.status_code == 200
    data = response.json()
    assert "bookings" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["bookings"]) == 2


def test_list_bookings_by_status(client: TestClient, _sample_bookings) -> None:
    """Test GET /api/bookings with status filter."""
    response = client.get("/api/bookings?status=PENDING")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(b["status"] == "PENDING" for b in data["bookings"])


def test_booking_list_includes_financial_summary(
    client: TestClient, _sample_bookings
) -> None:
    """Test that booking list includes financial calculations."""
    response = client.get("/api/bookings")

    assert response.status_code == 200
    data = response.json()

    # Find booking with both revenue and costs
    booking = next(b for b in data["bookings"] if b["id"] == "BL-2024-001")

    assert Decimal(booking["total_revenue"]) == Decimal("1000.00")
    assert Decimal(booking["total_costs"]) == Decimal("600.00")
    assert Decimal(booking["margin"]) == Decimal("400.00")
    assert Decimal(booking["commission"]) == Decimal("200.00")  # 50% of margin
    assert booking["document_count"] == 2  # 1 revenue + 1 cost


def test_get_booking_detail(client: TestClient, _sample_bookings) -> None:
    """Test GET /api/bookings/{bl_reference}."""
    response = client.get("/api/bookings/BL-2024-001")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "BL-2024-001"
    assert data["client_name"] == "Client A"
    assert data["client_nif"] == "B12345678"
    assert Decimal(data["total_revenue"]) == Decimal("1000.00")
    assert Decimal(data["total_costs"]) == Decimal("600.00")
    assert Decimal(data["margin"]) == Decimal("400.00")
    assert data["revenue_charge_count"] == 1
    assert data["cost_charge_count"] == 1


def test_get_booking_detail_not_found(client: TestClient) -> None:
    """Test GET /api/bookings/{bl_reference} when booking doesn't exist."""
    response = client.get("/api/bookings/NONEXISTENT")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_bookings_sorting(client: TestClient, _sample_bookings) -> None:
    """Test booking list sorting."""
    # Sort by created_at ascending
    response = client.get("/api/bookings?sort_by=created_at&descending=false")

    assert response.status_code == 200
    data = response.json()
    # First booking created should be first
    assert data["bookings"][0]["id"] == "BL-2024-001"


def test_booking_margin_percentage(client: TestClient, _sample_bookings) -> None:
    """Test margin percentage calculation in booking detail."""
    response = client.get("/api/bookings/BL-2024-001")

    assert response.status_code == 200
    data = response.json()
    # Margin: 400, Revenue: 1000 → 40%
    assert Decimal(data["margin_percentage"]) == Decimal("40.00")
