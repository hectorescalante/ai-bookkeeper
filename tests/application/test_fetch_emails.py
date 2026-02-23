"""Tests for FetchEmails use case."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.application.dtos.document_dtos import FetchEmailsRequest
from backend.application.use_cases.fetch_emails import FetchEmailsUseCase
from backend.domain.entities.configuration import Settings
from backend.domain.entities.document import Document
from backend.domain.value_objects import FileHash
from backend.ports.output.email_client import (
    EmailAttachment,
    EmailAuthError,
    EmailMessage,
)


def _connected_settings() -> Settings:
    settings = Settings.create()
    settings.set_outlook_configured(True, refresh_token="refresh-token")
    return settings


def test_fetch_emails_requires_connected_outlook(tmp_path: Path) -> None:
    document_repo = MagicMock()
    settings_repo = MagicMock()
    settings_repo.get.return_value = Settings.create()
    email_client = MagicMock()

    use_case = FetchEmailsUseCase(
        document_repo=document_repo,
        settings_repo=settings_repo,
        email_client=email_client,
        storage_root=tmp_path,
    )

    with pytest.raises(ValueError, match="Outlook is not connected"):
        use_case.execute(FetchEmailsRequest(max_messages=5))


def test_fetch_emails_imports_new_pdfs_and_skips_duplicates(tmp_path: Path) -> None:
    document_repo = MagicMock()
    settings_repo = MagicMock()
    settings_repo.get.return_value = _connected_settings()

    message = EmailMessage(
        message_id="msg-001",
        subject="Invoices",
        sender="ops@example.com",
        received_at=datetime.now(),
        attachments=(
            EmailAttachment(
                filename="invoice-a.pdf",
                content_type="application/pdf",
                content=b"pdf-content-a",
            ),
            EmailAttachment(
                filename="invoice-b.pdf",
                content_type="application/pdf",
                content=b"pdf-content-b",
            ),
        ),
    )
    email_client = MagicMock()
    email_client.fetch_messages_with_pdf_attachments.return_value = [message]

    existing = Document.create(
        filename="existing.pdf",
        file_hash=FileHash.sha256("existing-hash"),
    )
    document_repo.find_by_file_hash.side_effect = [None, existing]

    use_case = FetchEmailsUseCase(
        document_repo=document_repo,
        settings_repo=settings_repo,
        email_client=email_client,
        storage_root=tmp_path,
    )
    result = use_case.execute(FetchEmailsRequest(max_messages=10))

    assert result.scanned_messages == 1
    assert result.pdf_attachments_found == 2
    assert result.imported_documents == 1
    assert result.duplicate_documents == 1
    document_repo.save.assert_called_once()

    saved_document = document_repo.save.call_args[0][0]
    assert saved_document.storage_path is not None
    stored_path = Path(saved_document.storage_path)
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"pdf-content-a"


def test_fetch_emails_maps_auth_errors(tmp_path: Path) -> None:
    document_repo = MagicMock()
    settings_repo = MagicMock()
    settings_repo.get.return_value = _connected_settings()

    email_client = MagicMock()
    email_client.fetch_messages_with_pdf_attachments.side_effect = EmailAuthError(
        "token expired"
    )

    use_case = FetchEmailsUseCase(
        document_repo=document_repo,
        settings_repo=settings_repo,
        email_client=email_client,
        storage_root=tmp_path,
    )

    with pytest.raises(ValueError, match="authentication failed"):
        use_case.execute(FetchEmailsRequest(max_messages=5))
