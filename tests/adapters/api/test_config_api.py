"""Integration tests for configuration API endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.config.dependencies import get_ai_extractor
from backend.main import app


class _StubAIExtractor:
    def __init__(self, valid_keys: set[str]) -> None:
        self.valid_keys = valid_keys

    def test_connection(self, api_key: str) -> bool:
        return api_key in self.valid_keys


def test_configure_company(client: TestClient) -> None:
    """Test POST /api/config/company."""
    response = client.post(
        "/api/config/company",
        json={
            "name": "Test Company S.L.",
            "nif": "B12345678",
            "address": "Calle Mayor 1, Madrid",
            "contact_info": "info@test-company.com",
            "commission_rate": "0.50",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company S.L."
    assert data["nif"] == "B12345678"
    assert data["address"] == "Calle Mayor 1, Madrid"
    assert data["contact_info"] == "info@test-company.com"
    assert Decimal(data["commission_rate"]) == Decimal("0.50")
    assert data["is_configured"] is True
    assert "id" in data


def test_get_company(client: TestClient) -> None:
    """Test GET /api/config/company."""
    client.post(
        "/api/config/company",
        json={
            "name": "Test Company S.L.",
            "nif": "B12345678",
            "address": "Calle Mayor 1, Madrid",
            "contact_info": "info@test-company.com",
            "commission_rate": "0.50",
        },
    )

    # Then get it
    response = client.get("/api/config/company")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company S.L."
    assert data["nif"] == "B12345678"
    assert data["address"] == "Calle Mayor 1, Madrid"
    assert data["contact_info"] == "info@test-company.com"


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
            "gemini_api_key": "test-key-123",
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
            "gemini_api_key": "test-key-123",
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

def test_configure_agent(client: TestClient) -> None:
    response = client.post(
        "/api/config/agent",
        json={
            "name": "Hector Escalante",
            "email": "hector@example.com",
            "phone": "+34 600 000 000",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Hector Escalante"
    assert data["email"] == "hector@example.com"
    assert data["phone"] == "+34 600 000 000"
    assert "id" in data


def test_get_agent(client: TestClient) -> None:
    client.post(
        "/api/config/agent",
        json={
            "name": "Hector Escalante",
            "email": "hector@example.com",
            "phone": "+34 600 000 000",
        },
    )

    response = client.get("/api/config/agent")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Hector Escalante"
    assert data["email"] == "hector@example.com"
    assert data["phone"] == "+34 600 000 000"


def test_get_agent_not_configured(client: TestClient) -> None:
    response = client.get("/api/config/agent")
    assert response.status_code == 404
    assert "not configured" in response.json()["detail"].lower()


def test_test_gemini_connection_success_with_explicit_key(client: TestClient) -> None:
    app.dependency_overrides[get_ai_extractor] = lambda: _StubAIExtractor(
        valid_keys={"valid-key-123"}
    )
    try:
        response = client.post(
            "/api/config/settings/test-connection",
            json={"gemini_api_key": "valid-key-123"},
        )
    finally:
        app.dependency_overrides.pop(get_ai_extractor, None)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["message"] == "Valid connection"


def test_test_gemini_connection_invalid_key_returns_400(client: TestClient) -> None:
    app.dependency_overrides[get_ai_extractor] = lambda: _StubAIExtractor(
        valid_keys={"valid-key-123"}
    )
    try:
        response = client.post(
            "/api/config/settings/test-connection",
            json={"gemini_api_key": "bad-key"},
        )
    finally:
        app.dependency_overrides.pop(get_ai_extractor, None)

    assert response.status_code == 400
    assert "invalid gemini api key" in response.json()["detail"].lower()


def test_test_gemini_connection_uses_stored_key_when_payload_empty(
    client: TestClient,
) -> None:
    client.post(
        "/api/config/settings",
        json={
            "gemini_api_key": "stored-key-1",
            "default_export_path": "/exports",
            "extraction_prompt": "Extract invoice data",
        },
    )
    app.dependency_overrides[get_ai_extractor] = lambda: _StubAIExtractor(
        valid_keys={"stored-key-1"}
    )
    try:
        response = client.post("/api/config/settings/test-connection", json={})
    finally:
        app.dependency_overrides.pop(get_ai_extractor, None)

    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_test_gemini_connection_without_key_returns_400(client: TestClient) -> None:
    app.dependency_overrides[get_ai_extractor] = lambda: _StubAIExtractor(
        valid_keys={"valid-key-123"}
    )
    try:
        response = client.post("/api/config/settings/test-connection", json={})
    finally:
        app.dependency_overrides.pop(get_ai_extractor, None)

    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()


def test_update_company_commission_rate(client: TestClient) -> None:
    """Test updating company commission rate."""
    # Create company with 50% rate
    client.post(
        "/api/config/company",
        json={
            "name": "Test Company",
            "nif": "B12345678",
            "address": "Old address",
            "contact_info": "old-contact@test.com",
            "commission_rate": "0.50",
        },
    )

    # Update to 40% rate
    response = client.post(
        "/api/config/company",
        json={
            "name": "Test Company Updated",
            "nif": "B12345678",
            "address": "New address 123",
            "contact_info": "new-contact@test.com",
            "commission_rate": "0.40",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company Updated"
    assert data["address"] == "New address 123"
    assert data["contact_info"] == "new-contact@test.com"
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
