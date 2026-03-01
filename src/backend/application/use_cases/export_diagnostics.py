"""Use case to generate a diagnostics bundle for support."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.application.dtos import DiagnosticsExportResponse
from backend.config import get_settings
from backend.config.logging import get_runtime_logs_path, sanitize_for_logging, sanitize_log_line
from backend.domain.enums import ProcessingStatus
from backend.ports.output.repositories import (
    BookingRepository,
    ClientRepository,
    DocumentRepository,
    InvoiceRepository,
    ProviderRepository,
    SettingsRepository,
)

MAX_LOG_FILES = 5
MAX_BYTES_PER_LOG_FILE = 2 * 1024 * 1024
MAX_ERROR_LINES = 50


class ExportDiagnosticsUseCase:
    """Generate diagnostics zip bundle for user support workflows."""

    def __init__(
        self,
        settings_repo: SettingsRepository,
        booking_repo: BookingRepository,
        document_repo: DocumentRepository,
        invoice_repo: InvoiceRepository,
        client_repo: ClientRepository,
        provider_repo: ProviderRepository,
        *,
        primary_log_dir: Path | None = None,
        diagnostics_output_dir: Path | None = None,
    ) -> None:
        self.settings_repo = settings_repo
        self.booking_repo = booking_repo
        self.document_repo = document_repo
        self.invoice_repo = invoice_repo
        self.client_repo = client_repo
        self.provider_repo = provider_repo
        self.primary_log_dir = primary_log_dir
        self.diagnostics_output_dir = diagnostics_output_dir

    def execute(self) -> DiagnosticsExportResponse:
        """Export diagnostics into a zip file and return its location."""
        now = datetime.now(tz=UTC)
        file_stamp = now.strftime("%Y%m%d-%H%M%S")
        bundle_name = f"diagnostics-{file_stamp}.zip"
        target_directory = self._resolve_diagnostics_output_dir()
        target_directory.mkdir(parents=True, exist_ok=True)
        bundle_path = target_directory / bundle_name

        warnings: list[str] = []
        truncation_notes: list[str] = []
        collected_logs: list[tuple[str, str]] = []

        log_files = self._collect_recent_log_files()
        if not log_files:
            warnings.append("No log files were found; exported bundle contains metadata only.")

        with zipfile.ZipFile(bundle_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for log_path in log_files:
                try:
                    sanitized_content, was_truncated = self._read_sanitized_log_tail(
                        log_path, max_bytes=MAX_BYTES_PER_LOG_FILE
                    )
                except OSError:
                    warnings.append(f"Could not read log file: {log_path.name}")
                    continue

                collected_logs.append((log_path.name, sanitized_content))
                archive.writestr(f"logs/{log_path.name}", sanitized_content)

                if was_truncated:
                    truncation_notes.append(
                        f"{log_path.name}: exported tail limited to {MAX_BYTES_PER_LOG_FILE} bytes."
                    )

            if truncation_notes:
                archive.writestr(
                    "logs/TRUNCATION_NOTES.txt",
                    "\n".join(truncation_notes),
                )

            archive.writestr(
                "app-info.json",
                self._to_pretty_json(self._build_app_info()),
            )
            archive.writestr(
                "config-summary.json",
                self._to_pretty_json(self._build_config_summary()),
            )
            archive.writestr(
                "db-stats.json",
                self._to_pretty_json(self._build_db_stats()),
            )
            archive.writestr(
                "error-report.txt",
                self._build_error_report(collected_logs),
            )

        if truncation_notes:
            warnings.append("One or more large log files were truncated for export.")

        return DiagnosticsExportResponse(
            bundle_name=bundle_name,
            bundle_path=str(bundle_path),
            created_at=now.isoformat().replace("+00:00", "Z"),
            warnings=warnings,
        )

    def _collect_recent_log_files(self) -> list[Path]:
        candidates: list[Path] = []
        for directory in self._candidate_log_directories():
            if not directory.exists():
                continue
            candidates.extend(directory.glob("app-*.log"))

        unique_paths: dict[str, Path] = {}
        for path in candidates:
            try:
                unique_paths[str(path.resolve())] = path
            except OSError:
                unique_paths[str(path)] = path

        sorted_paths = sorted(
            unique_paths.values(),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return sorted_paths[:MAX_LOG_FILES]

    def _candidate_log_directories(self) -> list[Path]:
        app_settings = get_settings()
        primary = self.primary_log_dir or get_runtime_logs_path()
        legacy = app_settings.storage_path / "logs"

        directories: list[Path] = [primary]
        if legacy != primary:
            directories.append(legacy)
        return directories

    def _resolve_diagnostics_output_dir(self) -> Path:
        if self.diagnostics_output_dir is not None:
            return self.diagnostics_output_dir
        return get_settings().diagnostics_path

    def _read_sanitized_log_tail(self, log_path: Path, *, max_bytes: int) -> tuple[str, bool]:
        with log_path.open("rb") as handle:
            handle.seek(0, 2)
            file_size = handle.tell()
            start = max(file_size - max_bytes, 0)
            handle.seek(start)
            chunk = handle.read()

        was_truncated = start > 0
        if was_truncated:
            first_newline = chunk.find(b"\n")
            if first_newline >= 0:
                chunk = chunk[first_newline + 1 :]

        raw_text = chunk.decode("utf-8", errors="replace")
        sanitized_lines = [sanitize_log_line(line) for line in raw_text.splitlines()]
        return "\n".join(sanitized_lines), was_truncated

    def _build_app_info(self) -> dict[str, Any]:
        app_settings = get_settings()
        return sanitize_for_logging(
            {
                "app_name": app_settings.app_name,
                "app_env": app_settings.app_env,
                "backend_version": self._resolve_backend_version(),
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "system": platform.system(),
                "machine": platform.machine(),
            }
        )

    def _build_config_summary(self) -> dict[str, Any]:
        app_settings = get_settings()
        app_config = self.settings_repo.get()

        return sanitize_for_logging(
            {
                "app_env": app_settings.app_env,
                "log_level": app_settings.log_level,
                "log_format": app_settings.log_format,
                "storage_path": str(app_settings.storage_path),
                "diagnostics_path": str(app_settings.diagnostics_path),
                "icloud_enabled": app_settings.icloud_enabled,
                "outlook_configured": app_config.outlook_configured if app_config else False,
                "has_gemini_api_key": app_config.has_api_key if app_config else False,
                "default_export_path": app_config.default_export_path if app_config else "",
            }
        )

    def _build_db_stats(self) -> dict[str, Any]:
        documents_by_status = {
            status.value.lower(): len(self.document_repo.list_by_status(status))
            for status in ProcessingStatus
        }

        db_stats: dict[str, Any] = {
            "bookings": len(self.booking_repo.list_all()),
            "client_invoices": len(self.invoice_repo.list_client_invoices()),
            "provider_invoices": len(self.invoice_repo.list_provider_invoices()),
            "documents_total": sum(documents_by_status.values()),
            "documents_by_status": documents_by_status,
            "clients": len(self.client_repo.list_all()),
            "providers": len(self.provider_repo.list_all()),
        }
        return sanitize_for_logging(db_stats)

    def _build_error_report(self, collected_logs: list[tuple[str, str]]) -> str:
        extracted: list[str] = []

        for filename, log_text in collected_logs:
            for line in log_text.splitlines():
                parsed = self._safe_parse_json(line)
                if not parsed:
                    continue

                level = str(parsed.get("level", "")).upper()
                if level != "ERROR":
                    continue

                timestamp = str(parsed.get("timestamp", ""))
                component = str(parsed.get("component", ""))
                message = str(parsed.get("message", ""))
                context = parsed.get("context")
                exception_text = ""
                if isinstance(context, dict):
                    raw_exception = context.get("exception")
                    if isinstance(raw_exception, str):
                        exception_text = raw_exception.strip()

                entry = f"{timestamp} | {component} | {message} | source={filename}"
                if exception_text:
                    entry = f"{entry}\n{exception_text}"
                extracted.append(entry)

        if not extracted:
            return "No ERROR entries found in selected logs."

        tail_entries = extracted[-MAX_ERROR_LINES:]
        return "\n\n".join(tail_entries)

    def _resolve_backend_version(self) -> str:
        try:
            return importlib.metadata.version("ai-bookkeeper")
        except importlib.metadata.PackageNotFoundError:
            return "0.1.0"

    @staticmethod
    def _safe_parse_json(value: str) -> dict[str, Any] | None:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
        return None

    @staticmethod
    def _to_pretty_json(value: dict[str, Any]) -> str:
        return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
