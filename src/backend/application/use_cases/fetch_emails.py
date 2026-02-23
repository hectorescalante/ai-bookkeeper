"""Use case for fetching PDF attachments from Outlook inbox."""

import hashlib
from pathlib import Path
from re import sub

from backend.application.dtos.document_dtos import (
    FetchEmailsRequest,
    FetchEmailsResponse,
)
from backend.domain.entities.document import Document
from backend.domain.value_objects import EmailReference, FileHash
from backend.ports.output.email_client import (
    EmailAuthError,
    EmailClient,
    EmailClientError,
    EmailRateLimitError,
)
from backend.ports.output.repositories import DocumentRepository, SettingsRepository


class FetchEmailsUseCase:
    """Fetch unread Outlook emails and persist new PDF documents."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        settings_repo: SettingsRepository,
        email_client: EmailClient,
        storage_root: Path,
    ) -> None:
        self.document_repo = document_repo
        self.settings_repo = settings_repo
        self.email_client = email_client
        self.storage_root = storage_root

    def execute(self, request: FetchEmailsRequest) -> FetchEmailsResponse:
        """Execute the fetch emails workflow."""
        settings = self.settings_repo.get()
        if not settings or not settings.outlook_configured or not settings.outlook_refresh_token:
            raise ValueError("Outlook is not connected. Configure Outlook in Settings first.")

        try:
            messages = self.email_client.fetch_messages_with_pdf_attachments(
                max_messages=request.max_messages
            )
        except EmailAuthError as exc:
            raise ValueError("Outlook authentication failed. Reconnect Outlook in Settings.") from exc
        except EmailRateLimitError as exc:
            retry_after = (
                f" Try again in ~{exc.retry_after_seconds} seconds."
                if exc.retry_after_seconds is not None
                else ""
            )
            raise ValueError(f"Outlook rate limit reached.{retry_after}") from exc
        except EmailClientError as exc:
            raise ValueError(f"Could not fetch Outlook emails: {exc}") from exc

        imported_documents = 0
        duplicate_documents = 0
        pdf_attachments_found = 0

        for message in messages:
            for attachment in message.attachments:
                pdf_attachments_found += 1
                file_hash = FileHash.sha256(
                    hashlib.sha256(attachment.content).hexdigest()
                )

                existing = self.document_repo.find_by_file_hash(file_hash)
                if existing is not None:
                    duplicate_documents += 1
                    continue

                stored_path = self._store_attachment(
                    filename=attachment.filename,
                    hash_prefix=file_hash.value[:12],
                    content=attachment.content,
                )
                document = Document.create(
                    filename=self._sanitize_filename(attachment.filename),
                    file_hash=file_hash,
                    email_reference=EmailReference(
                        message_id=message.message_id,
                        subject=message.subject,
                        sender=message.sender,
                        received_at=message.received_at,
                    ),
                    storage_path=str(stored_path),
                )
                self.document_repo.save(document)
                imported_documents += 1

        return FetchEmailsResponse(
            scanned_messages=len(messages),
            pdf_attachments_found=pdf_attachments_found,
            imported_documents=imported_documents,
            duplicate_documents=duplicate_documents,
        )

    def _store_attachment(self, filename: str, hash_prefix: str, content: bytes) -> Path:
        storage_dir = self.storage_root / "pdfs"
        storage_dir.mkdir(parents=True, exist_ok=True)

        safe_name = self._sanitize_filename(filename)
        stored_name = f"{hash_prefix}-{safe_name}"
        file_path = storage_dir / stored_name
        file_path.write_bytes(content)
        return file_path

    def _sanitize_filename(self, filename: str) -> str:
        raw = filename.strip() or "attachment.pdf"
        sanitized = sub(r"[^A-Za-z0-9._-]", "_", raw).strip("._")
        if not sanitized:
            sanitized = "attachment.pdf"
        if not sanitized.lower().endswith(".pdf"):
            sanitized = f"{sanitized}.pdf"
        return sanitized
