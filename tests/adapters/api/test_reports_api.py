"""Integration tests for reports API endpoints."""

from datetime import datetime
from decimal import Decimal
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from backend.domain.entities.booking import Booking
from backend.domain.enums import ChargeCategory, ProviderType
from backend.domain.value_objects import BookingCharge, ClientInfo, Money


@pytest.fixture
def sample_report_bookings(db_session):
    """Create sample bookings for report generation tests."""
    from uuid import uuid4

    from backend.adapters.persistence.models.party import ClientModel
    from backend.adapters.persistence.repositories.booking_repository import (
        SqlAlchemyBookingRepository,
    )

    client_id1 = uuid4()
    client_id2 = uuid4()

    db_session.add_all(
        [
            ClientModel(
                id=client_id1,
                name="Client A",
                nif="B12345678",
                created_at=datetime.now(),
            ),
            ClientModel(
                id=client_id2,
                name="Client B",
                nif="B87654321",
                created_at=datetime.now(),
            ),
        ]
    )
    db_session.commit()

    repo = SqlAlchemyBookingRepository(db_session)

    booking1 = Booking.create("BL-2024-001")
    booking1.created_at = datetime(2024, 1, 5)
    booking1.update_client(ClientInfo(client_id1, "Client A", "B12345678"))
    booking1.add_revenue_charge(
        BookingCharge(
            booking_id="BL-2024-001",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container="CONT001",
            description="Revenue 1",
            amount=Money(Decimal("1000.00")),
        )
    )
    booking1.add_cost_charge(
        BookingCharge(
            booking_id="BL-2024-001",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.CARRIER,
            container="CONT001",
            description="Cost 1",
            amount=Money(Decimal("600.00")),
        )
    )
    booking1.mark_complete()
    repo.save(booking1)

    booking2 = Booking.create("BL-2024-002")
    booking2.created_at = datetime(2024, 1, 25)
    booking2.update_client(ClientInfo(client_id2, "Client B", "B87654321"))
    booking2.add_revenue_charge(
        BookingCharge(
            booking_id="BL-2024-002",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.HANDLING,
            provider_type=None,
            container=None,
            description="Revenue 2",
            amount=Money(Decimal("500.00")),
        )
    )
    booking2.add_cost_charge(
        BookingCharge(
            booking_id="BL-2024-002",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.HANDLING,
            provider_type=ProviderType.INSPECTION,
            container=None,
            description="Cost 2",
            amount=Money(Decimal("100.00")),
        )
    )
    repo.save(booking2)

    booking3 = Booking.create("BL-2024-003")
    booking3.created_at = datetime(2024, 2, 2)
    booking3.update_client(ClientInfo(client_id1, "Client A", "B12345678"))
    booking3.add_revenue_charge(
        BookingCharge(
            booking_id="BL-2024-003",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.TRANSPORT,
            provider_type=None,
            container=None,
            description="Revenue 3",
            amount=Money(Decimal("1200.00")),
        )
    )
    booking3.add_cost_charge(
        BookingCharge(
            booking_id="BL-2024-003",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.TRANSPORT,
            provider_type=ProviderType.CARRIER,
            container=None,
            description="Cost 3",
            amount=Money(Decimal("700.00")),
        )
    )
    booking3.mark_complete()
    repo.save(booking3)

    db_session.commit()
    return [booking1, booking2, booking3]


def test_generate_commission_report(client: TestClient, sample_report_bookings) -> None:
    _ = sample_report_bookings
    response = client.post("/api/reports/commission", json={})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 3
    assert payload["totals"]["booking_count"] == 3
    assert Decimal(payload["totals"]["total_revenue"]) == Decimal("2700.00")
    assert Decimal(payload["totals"]["total_costs"]) == Decimal("1400.00")
    assert Decimal(payload["totals"]["total_margin"]) == Decimal("1300.00")
    assert Decimal(payload["totals"]["total_commission"]) == Decimal("650.00")


def test_generate_commission_report_filters_by_status(
    client: TestClient, sample_report_bookings
) -> None:
    _ = sample_report_bookings
    response = client.post("/api/reports/commission", json={"status": "COMPLETE"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert payload["totals"]["booking_count"] == 2
    assert all(item["status"] == "COMPLETE" for item in payload["items"])


def test_generate_commission_report_filters_by_date_range(
    client: TestClient, sample_report_bookings
) -> None:
    _ = sample_report_bookings
    response = client.post(
        "/api/reports/commission",
        json={"date_from": "2024-02-01", "date_to": "2024-02-28"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["booking_id"] == "BL-2024-003"


def test_generate_commission_report_invalid_status_returns_400(client: TestClient) -> None:
    response = client.post("/api/reports/commission", json={"status": "INVALID"})
    assert response.status_code == 400
    assert "invalid status" in response.json()["detail"].lower()


def test_generate_commission_report_invalid_date_range_returns_400(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/reports/commission",
        json={"date_from": "2024-03-01", "date_to": "2024-02-01"},
    )
    assert response.status_code == 400
    assert "date_from" in response.json()["detail"].lower()


def test_export_commission_report_returns_excel_file(
    client: TestClient, sample_report_bookings
) -> None:
    _ = sample_report_bookings
    response = client.post(
        "/api/reports/export",
        json={"status": "COMPLETE", "file_name": "commission-report"},
    )

    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment;" in response.headers["content-disposition"]
    assert "commission-report.xlsx" in response.headers["content-disposition"]

    workbook = load_workbook(filename=BytesIO(response.content))
    sheet = workbook.active
    assert sheet is not None
    assert sheet["A1"].value == "Booking ID"
    first_column_values = [cell.value for cell in sheet["A"] if cell.value]
    assert "TOTAL" in first_column_values
