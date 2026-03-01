"""Tests for diagnostics bundle export use case."""

from __future__ import annotations

import json
import zipfile
from unittest.mock import MagicMock

from backend.application.use_cases.export_diagnostics import ExportDiagnosticsUseCase
from backend.domain.entities.configuration import Settings
from backend.domain.enums import ProcessingStatus


def _build_use_case(
    *,
    logs_dir,
    diagnostics_dir,
    has_settings: bool = True,
) -> ExportDiagnosticsUseCase:
    settings_repo = MagicMock()
    if has_settings:
        settings = Settings.create()
        settings.set_api_key("secret-key")
        settings.default_export_path = "/tmp/exports"
        settings_repo.get.return_value = settings
    else:
        settings_repo.get.return_value = None

    booking_repo = MagicMock()
    booking_repo.list_all.return_value = [object(), object()]

    invoice_repo = MagicMock()
    invoice_repo.list_client_invoices.return_value = [object()]
    invoice_repo.list_provider_invoices.return_value = [object(), object()]

    client_repo = MagicMock()
    client_repo.list_all.return_value = [object(), object(), object()]

    provider_repo = MagicMock()
    provider_repo.list_all.return_value = [object()]

    document_repo = MagicMock()
    status_counts = {
        ProcessingStatus.PENDING: 2,
        ProcessingStatus.PROCESSING: 1,
        ProcessingStatus.PROCESSED: 3,
        ProcessingStatus.ERROR: 1,
    }
    document_repo.list_by_status.side_effect = (
        lambda status: [object()] * status_counts[status]
    )

    return ExportDiagnosticsUseCase(
        settings_repo=settings_repo,
        booking_repo=booking_repo,
        document_repo=document_repo,
        invoice_repo=invoice_repo,
        client_repo=client_repo,
        provider_repo=provider_repo,
        primary_log_dir=logs_dir,
        diagnostics_output_dir=diagnostics_dir,
    )


def test_export_diagnostics_creates_zip_with_expected_files(tmp_path) -> None:
    logs_dir = tmp_path / "logs"
    diagnostics_dir = tmp_path / "diagnostics"
    logs_dir.mkdir(parents=True)
    diagnostics_dir.mkdir(parents=True)

    log_file = logs_dir / "app-2026-03-01.log"
    log_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-03-01T12:00:00.000Z",
                        "level": "INFO",
                        "component": "tests",
                        "message": "startup ok",
                        "context": {"request_id": "abc"},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-03-01T12:10:00.000Z",
                        "level": "ERROR",
                        "component": "tests",
                        "message": "processing failed token=abc",
                        "context": {
                            "api_key": "real-secret",
                            "exception": "Traceback line 1",
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    use_case = _build_use_case(logs_dir=logs_dir, diagnostics_dir=diagnostics_dir)
    result = use_case.execute()

    bundle_path = diagnostics_dir / result.bundle_name
    assert result.bundle_path == str(bundle_path)
    assert bundle_path.exists()
    assert result.warnings == []

    with zipfile.ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
        assert "app-info.json" in names
        assert "config-summary.json" in names
        assert "db-stats.json" in names
        assert "error-report.txt" in names
        assert "logs/app-2026-03-01.log" in names

        exported_log = archive.read("logs/app-2026-03-01.log").decode("utf-8")
        assert "real-secret" not in exported_log
        assert "[REDACTED]" in exported_log

        error_report = archive.read("error-report.txt").decode("utf-8")
        assert "processing failed" in error_report
        assert "Traceback line 1" in error_report


def test_export_diagnostics_handles_missing_logs(tmp_path) -> None:
    logs_dir = tmp_path / "logs-empty"
    diagnostics_dir = tmp_path / "diagnostics"
    logs_dir.mkdir(parents=True)
    diagnostics_dir.mkdir(parents=True)

    use_case = _build_use_case(
        logs_dir=logs_dir,
        diagnostics_dir=diagnostics_dir,
        has_settings=False,
    )
    result = use_case.execute()

    assert len(result.warnings) == 1
    assert "No log files were found" in result.warnings[0]

    with zipfile.ZipFile(result.bundle_path) as archive:
        error_report = archive.read("error-report.txt").decode("utf-8")
        assert "No ERROR entries found" in error_report
