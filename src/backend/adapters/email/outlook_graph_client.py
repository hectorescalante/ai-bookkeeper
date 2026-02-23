"""Outlook email client adapter backed by Microsoft Graph."""

from base64 import b64decode
from datetime import datetime
from typing import Any

import httpx

from backend.ports.output.email_client import (
    EmailAttachment,
    EmailAuthError,
    EmailClient,
    EmailClientError,
    EmailMessage,
    EmailRateLimitError,
)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MAIL_SCOPE = "offline_access Mail.Read User.Read"


class OutlookGraphEmailClient(EmailClient):
    """Email client implementation that reads Outlook inbox via Microsoft Graph."""

    def __init__(
        self,
        client_id: str,
        tenant_id: str,
        refresh_token: str,
        redirect_uri: str | None = None,
    ) -> None:
        self._client_id = client_id
        self._tenant_id = tenant_id
        self._refresh_token = refresh_token
        self._redirect_uri = redirect_uri

    def fetch_messages_with_pdf_attachments(
        self, max_messages: int = 25
    ) -> list[EmailMessage]:
        """Fetch unread messages with PDF attachments from Outlook inbox."""
        access_token = self._refresh_access_token()
        messages = self._list_unread_messages(
            access_token=access_token,
            max_messages=max_messages,
        )

        result: list[EmailMessage] = []
        for message in messages:
            message_id = str(message.get("id", "")).strip()
            if not message_id:
                continue

            attachments = self._list_pdf_attachments(
                access_token=access_token,
                message_id=message_id,
            )
            if not attachments:
                continue

            result.append(
                EmailMessage(
                    message_id=message_id,
                    subject=str(message.get("subject", "")),
                    sender=self._extract_sender(message),
                    received_at=self._parse_received_at(message.get("receivedDateTime")),
                    attachments=tuple(attachments),
                )
            )
        return result

    def _refresh_access_token(self) -> str:
        if not self._client_id:
            raise EmailAuthError("AZURE_CLIENT_ID is not configured")
        if not self._refresh_token:
            raise EmailAuthError("Outlook refresh token is missing")

        token_url = (
            f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"
        )
        payload = {
            "client_id": self._client_id,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "scope": MAIL_SCOPE,
        }
        if self._redirect_uri:
            payload["redirect_uri"] = self._redirect_uri

        try:
            with httpx.Client(timeout=20) as client:
                response = client.post(token_url, data=payload)
        except httpx.HTTPError as exc:
            raise EmailClientError(f"Failed to reach Outlook token endpoint: {exc}") from exc

        if response.status_code in {400, 401, 403}:
            raise EmailAuthError("Outlook refresh token is invalid or expired")
        if response.status_code == 429:
            retry = self._parse_retry_after(response.headers.get("Retry-After"))
            raise EmailRateLimitError(retry_after_seconds=retry)
        if response.status_code >= 400:
            raise EmailClientError(
                f"Outlook token request failed with status {response.status_code}"
            )

        payload_json = response.json()
        access_token = payload_json.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise EmailClientError("Outlook token response did not include access_token")

        maybe_refresh_token = payload_json.get("refresh_token")
        if isinstance(maybe_refresh_token, str) and maybe_refresh_token:
            self._refresh_token = maybe_refresh_token

        return access_token

    def _list_unread_messages(
        self, access_token: str, max_messages: int
    ) -> list[dict[str, Any]]:
        url = f"{GRAPH_BASE_URL}/me/messages"
        params = {
            "$top": str(max_messages),
            "$filter": "isRead eq false and hasAttachments eq true",
            "$select": "id,subject,from,receivedDateTime",
            "$orderby": "receivedDateTime desc",
        }

        response = self._graph_get(
            url=url,
            access_token=access_token,
            params=params,
        )
        payload = response.json()
        value = payload.get("value", [])
        if not isinstance(value, list):
            raise EmailClientError("Outlook messages response has invalid format")
        return [item for item in value if isinstance(item, dict)]

    def _list_pdf_attachments(
        self, access_token: str, message_id: str
    ) -> list[EmailAttachment]:
        url = f"{GRAPH_BASE_URL}/me/messages/{message_id}/attachments"
        params = {
            "$select": "name,contentType,contentBytes,@odata.type,isInline",
        }
        response = self._graph_get(
            url=url,
            access_token=access_token,
            params=params,
        )
        payload = response.json()
        value = payload.get("value", [])
        if not isinstance(value, list):
            raise EmailClientError("Outlook attachments response has invalid format")

        result: list[EmailAttachment] = []
        for item in value:
            if not isinstance(item, dict):
                continue

            odata_type = str(item.get("@odata.type", ""))
            if "fileAttachment" not in odata_type:
                continue
            if bool(item.get("isInline")):
                continue

            filename = str(item.get("name", "")).strip()
            content_type = str(item.get("contentType", "")).strip()
            if not self._is_pdf(filename=filename, content_type=content_type):
                continue

            content_b64 = item.get("contentBytes")
            if not isinstance(content_b64, str) or not content_b64:
                continue

            try:
                content = b64decode(content_b64)
            except ValueError:
                continue

            result.append(
                EmailAttachment(
                    filename=filename or "attachment.pdf",
                    content_type=content_type or "application/pdf",
                    content=content,
                )
            )
        return result

    def _graph_get(
        self,
        url: str,
        access_token: str,
        params: dict[str, str],
    ) -> httpx.Response:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise EmailClientError(f"Failed to reach Outlook Graph API: {exc}") from exc

        if response.status_code in {401, 403}:
            raise EmailAuthError("Outlook token is unauthorized for mailbox access")
        if response.status_code == 429:
            retry = self._parse_retry_after(response.headers.get("Retry-After"))
            raise EmailRateLimitError(retry_after_seconds=retry)
        if response.status_code >= 400:
            raise EmailClientError(
                f"Outlook Graph request failed with status {response.status_code}"
            )
        return response

    def _extract_sender(self, message: dict[str, Any]) -> str:
        from_data = message.get("from", {})
        if not isinstance(from_data, dict):
            return ""
        email_address = from_data.get("emailAddress", {})
        if not isinstance(email_address, dict):
            return ""
        sender = email_address.get("address")
        return str(sender) if sender is not None else ""

    def _parse_received_at(self, raw: Any) -> datetime:
        if not isinstance(raw, str):
            return datetime.now()
        normalized = raw.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.now()

    def _is_pdf(self, filename: str, content_type: str) -> bool:
        if content_type.lower() == "application/pdf":
            return True
        return filename.lower().endswith(".pdf")

    def _parse_retry_after(self, value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None
