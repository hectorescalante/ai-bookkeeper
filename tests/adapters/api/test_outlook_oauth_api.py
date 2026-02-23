"""Integration tests for Outlook OAuth API endpoints."""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from backend.adapters.email.outlook_oauth import OutlookAuthSession
from backend.config.dependencies import get_outlook_oauth_manager
from backend.main import app


class _StubOutlookOAuthManager:
    def __init__(
        self,
        authorization_url: str = "https://login.microsoftonline.com/fake-auth",
        refresh_token: str = "refresh-token-123",
        complete_error: Exception | None = None,
    ) -> None:
        self.authorization_url = authorization_url
        self.refresh_token = refresh_token
        self.complete_error = complete_error

    def start_authorization(self) -> OutlookAuthSession:
        return OutlookAuthSession(
            state="stub-state",
            authorization_url=self.authorization_url,
            flow_payload={"state": "stub-state", "nonce": "nonce"},
            expires_at=datetime.now() + timedelta(minutes=15),
        )

    def complete_authorization(
        self,
        flow_payload: dict[str, str],
        callback_params: dict[str, str],
    ) -> str:
        if self.complete_error is not None:
            raise self.complete_error
        assert "state" in flow_payload
        assert "state" in callback_params
        return self.refresh_token


def test_connect_outlook_returns_authorization_url(client: TestClient) -> None:
    app.dependency_overrides[get_outlook_oauth_manager] = lambda: _StubOutlookOAuthManager(
        authorization_url="https://example.test/oauth"
    )
    try:
        response = client.get("/api/settings/outlook/connect")
    finally:
        app.dependency_overrides.pop(get_outlook_oauth_manager, None)

    assert response.status_code == 200
    assert response.json()["authorization_url"] == "https://example.test/oauth"


def test_outlook_callback_persists_connected_settings(client: TestClient) -> None:
    app.dependency_overrides[get_outlook_oauth_manager] = lambda: _StubOutlookOAuthManager(
        refresh_token="rt-xyz"
    )
    try:
        connect_response = client.get("/api/settings/outlook/connect")
        assert connect_response.status_code == 200
        callback_response = client.get(
            "/api/settings/outlook/callback?state=stub-state&code=auth-code"
        )
    finally:
        app.dependency_overrides.pop(get_outlook_oauth_manager, None)

    assert callback_response.status_code == 200
    assert "Outlook connected successfully" in callback_response.text

    settings_response = client.get("/api/config/settings")
    assert settings_response.status_code == 200
    assert settings_response.json()["outlook_configured"] is True


def test_outlook_callback_error_returns_400(client: TestClient) -> None:
    app.dependency_overrides[get_outlook_oauth_manager] = lambda: _StubOutlookOAuthManager(
        complete_error=ValueError("<script>alert('xss')</script>")
    )
    try:
        connect_response = client.get("/api/settings/outlook/connect")
        assert connect_response.status_code == 200
        callback_response = client.get(
            "/api/settings/outlook/callback?state=stub-state&code=bad-code"
        )
    finally:
        app.dependency_overrides.pop(get_outlook_oauth_manager, None)

    assert callback_response.status_code == 400
    assert "Outlook connection failed" in callback_response.text
    assert "<script>" not in callback_response.text
    assert "&lt;script&gt;" in callback_response.text


def test_outlook_callback_state_is_one_time_use(client: TestClient) -> None:
    app.dependency_overrides[get_outlook_oauth_manager] = lambda: _StubOutlookOAuthManager(
        refresh_token="rt-once"
    )
    try:
        connect_response = client.get("/api/settings/outlook/connect")
        assert connect_response.status_code == 200

        first_callback = client.get(
            "/api/settings/outlook/callback?state=stub-state&code=ok-code"
        )
        second_callback = client.get(
            "/api/settings/outlook/callback?state=stub-state&code=replay-code"
        )
    finally:
        app.dependency_overrides.pop(get_outlook_oauth_manager, None)

    assert first_callback.status_code == 200
    assert second_callback.status_code == 400
    assert "OAuth session expired" in second_callback.text


def test_disconnect_outlook_clears_connection_flag(client: TestClient) -> None:
    app.dependency_overrides[get_outlook_oauth_manager] = lambda: _StubOutlookOAuthManager(
        refresh_token="rt-123"
    )
    try:
        # Seed a connected state via connect + callback
        connect_response = client.get("/api/settings/outlook/connect")
        assert connect_response.status_code == 200
        client.get("/api/settings/outlook/callback?state=stub-state&code=seed-code")
    finally:
        app.dependency_overrides.pop(get_outlook_oauth_manager, None)

    disconnect_response = client.post("/api/settings/outlook/disconnect")
    assert disconnect_response.status_code == 200
    assert disconnect_response.json()["outlook_configured"] is False

    settings_response = client.get("/api/config/settings")
    assert settings_response.status_code == 200
    assert settings_response.json()["outlook_configured"] is False
