"""Integration tests for configuration API endpoints."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


def test_configure_company(client: TestClient) -> None:
    """Test POST /api/config/company."""
    # Configure company
    response = client.post(
        "/api/config/company",
        json={
            "name": "Test Company S.L.",
            "nif": "B12345678",
            "commission_rate": "0.50",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company S.L."
    assert data["nif"] == "B12345678"
    assert Decimal(data["commission_rate"]) == Decimal("0.50")
    assert data["is_configured"] is True
    assert "id" in data


def test_get_company(client: TestClient) -> None:
    """Test GET /api/config/company."""
    # First configure company
    client.post(
        "/api/config/company",
        json={
            "name": "Test Company S.L.",
            "nif": "B12345678",
            "commission_rate": "0.50",
        },
    )

    # Then get it
    response = client.get("/api/config/company")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company S.L."
    assert data["nif"] == "B12345678"


def test_get_company_not_configured(client: TestClient) -> None:
    """Test GET /api/config/company when not configured."""
    response = client.get("/api/config/company")

    assert response.status_code == 404
    assert "not configured" in response.json()["detail"].lower()


def test_configure_settings(client: TestClient) -> None:
    """Test POST /api/config/settings."""
    response = client.post(
        "/api/config/settings",
        json={
            "anthropic_api_key": "test-key-123",
            "default_export_path": "/exports",
            "extraction_prompt": "Extract invoice data",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["has_api_key"] is True
    assert data["extraction_prompt"] == "Extract invoice data"
    assert data["default_export_path"] == "/exports"


def test_get_settings(client: TestClient) -> None:
    """Test GET /api/config/settings."""
    # First configure settings
    client.post(
        "/api/config/settings",
        json={
            "anthropic_api_key": "test-key-123",
            "default_export_path": "/exports",
            "extraction_prompt": "Extract invoice data",
        },
    )

    # Then get them
    response = client.get("/api/config/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["has_api_key"] is True
    assert data["extraction_prompt"] == "Extract invoice data"


def test_update_company_commission_rate(client: TestClient) -> None:
    """Test updating company commission rate."""
    # Create company with 50% rate
    client.post(
        "/api/config/company",
        json={
            "name": "Test Company",
            "nif": "B12345678",
            "commission_rate": "0.50",
        },
    )

    # Update to 40% rate
    response = client.post(
        "/api/config/company",
        json={
            "name": "Test Company Updated",
            "nif": "B12345678",
            "commission_rate": "0.40",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company Updated"
    assert Decimal(data["commission_rate"]) == Decimal("0.40")


def test_invalid_commission_rate(client: TestClient) -> None:
    """Test validation of commission rate."""
    response = client.post(
        "/api/config/company",
        json={
            "name": "Test Company",
            "nif": "B12345678",
            "commission_rate": "1.5",  # Invalid: > 1.0
        },
    )

    assert response.status_code == 422  # Validation error
