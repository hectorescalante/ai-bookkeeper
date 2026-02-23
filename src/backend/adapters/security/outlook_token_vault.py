"""Outlook refresh token vault with macOS Keychain support."""

import os
import subprocess
import sys
from uuid import UUID

KEYCHAIN_SERVICE = "ai-bookkeeper.outlook.refresh-token"
KEYCHAIN_REF_PREFIX = "keychain://ai-bookkeeper/outlook-refresh-token/"


class OutlookRefreshTokenVault:
    """Store/retrieve Outlook refresh tokens, preferring macOS Keychain."""

    def __init__(self) -> None:
        self._use_keychain = self._is_keychain_enabled()

    def save_token(self, settings_id: UUID, refresh_token: str) -> str:
        """Persist refresh token and return DB-storable token reference."""
        if not refresh_token:
            return ""
        if not self._use_keychain:
            return refresh_token

        account = self._account_for_settings(settings_id)
        result = subprocess.run(
            [
                "security",
                "add-generic-password",
                "-a",
                account,
                "-s",
                KEYCHAIN_SERVICE,
                "-w",
                refresh_token,
                "-U",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to store Outlook token in macOS Keychain")

        return f"{KEYCHAIN_REF_PREFIX}{account}"

    def is_keychain_reference(self, stored_value: str) -> bool:
        """Check whether stored DB value is a keychain reference marker."""
        return stored_value.startswith(KEYCHAIN_REF_PREFIX)

    def load_token(self, settings_id: UUID, stored_value: str) -> str:
        """Resolve refresh token from DB value/reference."""
        if not stored_value:
            return ""
        if not self._use_keychain:
            return stored_value
        if not stored_value.startswith(KEYCHAIN_REF_PREFIX):
            # Legacy plaintext value from before keychain migration.
            return stored_value

        account = stored_value.removeprefix(KEYCHAIN_REF_PREFIX).strip()
        if not account:
            account = self._account_for_settings(settings_id)

        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                account,
                "-s",
                KEYCHAIN_SERVICE,
                "-w",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    def delete_token(self, settings_id: UUID, stored_value: str) -> None:
        """Delete token from keychain when disconnecting Outlook."""
        if not self._use_keychain:
            return

        account = (
            stored_value.removeprefix(KEYCHAIN_REF_PREFIX).strip()
            if stored_value.startswith(KEYCHAIN_REF_PREFIX)
            else self._account_for_settings(settings_id)
        )
        if not account:
            return

        subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-a",
                account,
                "-s",
                KEYCHAIN_SERVICE,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def _is_keychain_enabled(self) -> bool:
        if sys.platform != "darwin":
            return False
        return not os.getenv("PYTEST_CURRENT_TEST")

    def _account_for_settings(self, settings_id: UUID) -> str:
        return f"settings-{settings_id}"
