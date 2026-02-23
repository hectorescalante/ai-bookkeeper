"""Outlook OAuth helper for authorization-code flow using MSAL."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import msal

OAUTH_SCOPES = ["offline_access", "Mail.Read", "Mail.ReadBasic", "User.Read"]
FLOW_TTL_MINUTES = 15


@dataclass(frozen=True)
class OutlookAuthSession:
    """Single OAuth session payload to be persisted server-side."""

    state: str
    authorization_url: str
    flow_payload: dict[str, Any]
    expires_at: datetime


class OutlookOAuthManager:
    """Create and complete Outlook OAuth authorization sessions."""

    def __init__(self, client_id: str, tenant_id: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.redirect_uri = redirect_uri
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self._app = msal.PublicClientApplication(
            client_id=client_id,
            authority=authority,
        )

    def start_authorization(self) -> OutlookAuthSession:
        """Start OAuth flow and return session info for persistence."""
        if not self.client_id:
            raise ValueError("AZURE_CLIENT_ID is not configured")

        flow = self._app.initiate_auth_code_flow(
            scopes=OAUTH_SCOPES,
            redirect_uri=self.redirect_uri,
        )
        state = flow.get("state")
        auth_uri = flow.get("auth_uri")

        if not isinstance(state, str) or not state:
            raise ValueError("Failed to initialize Outlook OAuth state")
        if not isinstance(auth_uri, str) or not auth_uri:
            raise ValueError("Failed to build Outlook OAuth URL")

        return OutlookAuthSession(
            state=state,
            authorization_url=auth_uri,
            flow_payload=flow,
            expires_at=(datetime.now(UTC) + timedelta(minutes=FLOW_TTL_MINUTES)).replace(
                tzinfo=None
            ),
        )

    def complete_authorization(
        self,
        flow_payload: dict[str, Any],
        callback_params: dict[str, str],
    ) -> str:
        """Complete OAuth callback and return refresh token."""
        if "error" in callback_params:
            error_description = callback_params.get("error_description", "OAuth error")
            raise ValueError(error_description)

        result = self._app.acquire_token_by_auth_code_flow(
            auth_code_flow=flow_payload,
            auth_response=callback_params,
        )

        if not isinstance(result, dict):
            raise ValueError("Invalid Outlook OAuth response")

        if "error" in result:
            error_description = str(
                result.get("error_description") or result.get("error")
            ).strip()
            raise ValueError(error_description or "Outlook OAuth failed")

        refresh_token = result.get("refresh_token")
        if not isinstance(refresh_token, str) or not refresh_token:
            raise ValueError(
                "Outlook OAuth did not return refresh token. Ensure offline_access scope is allowed."
            )
        return refresh_token
