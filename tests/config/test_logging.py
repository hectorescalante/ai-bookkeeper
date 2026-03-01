"""Tests for centralized logging configuration and sanitization."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, date, datetime, timedelta

from backend.config.logging import (
    LOG_FILE_PREFIX,
    cleanup_old_logs,
    sanitize_for_logging,
    sanitize_log_line,
    setup_logging,
)
from backend.config.settings import Settings


def test_sanitize_for_logging_redacts_sensitive_keys() -> None:
    payload = {
        "api_key": "secret-value",
        "nested": {"email": "person@example.com", "safe": "value"},
        "items": [{"token": "abc"}, {"normal": "ok"}],
    }

    sanitized = sanitize_for_logging(payload)
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["email"] == "[REDACTED]"
    assert sanitized["nested"]["safe"] == "value"
    assert sanitized["items"][0]["token"] == "[REDACTED]"
    assert sanitized["items"][1]["normal"] == "ok"


def test_sanitize_log_line_handles_json_and_plain_text() -> None:
    json_line = (
        '{"level":"ERROR","message":"token=abc","context":{"authorization":"Bearer foo"}}'
    )
    plain_text_line = "Failed with token=abc and password=secret"

    sanitized_json_line = sanitize_log_line(json_line)
    parsed = json.loads(sanitized_json_line)
    assert parsed["context"]["authorization"] == "[REDACTED]"
    assert "abc" not in sanitized_json_line

    sanitized_plain_text = sanitize_log_line(plain_text_line)
    assert "secret" not in sanitized_plain_text
    assert "[REDACTED]" in sanitized_plain_text


def test_cleanup_old_logs_removes_files_outside_retention(tmp_path) -> None:
    old_log = tmp_path / f"{LOG_FILE_PREFIX}-2020-01-01.log"
    old_log.write_text("old", encoding="utf-8")
    old_timestamp = (datetime.now(tz=UTC) - timedelta(days=45)).timestamp()
    os.utime(old_log, (old_timestamp, old_timestamp))

    new_log = tmp_path / f"{LOG_FILE_PREFIX}-{date.today().isoformat()}.log"
    new_log.write_text("new", encoding="utf-8")

    cleanup_old_logs(tmp_path, retention_days=30)

    assert not old_log.exists()
    assert new_log.exists()


def test_setup_logging_writes_json_and_redacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("backend.config.logging.get_runtime_logs_path", lambda: tmp_path)
    settings = Settings(app_env="development", log_level="INFO")

    setup_logging(settings, force_reconfigure=True)

    logger = logging.getLogger("tests.logging")
    logger.info(
        "connection failed token=abc",
        extra={"api_key": "top-secret", "request_id": "req-1"},
    )

    for handler in logging.getLogger().handlers:
        handler.flush()

    log_file = tmp_path / f"{LOG_FILE_PREFIX}-{date.today().isoformat()}.log"
    content = log_file.read_text(encoding="utf-8")
    assert "top-secret" not in content
    assert "[REDACTED]" in content
    parsed_line = json.loads(content.strip().splitlines()[-1])
    assert parsed_line["level"] == "INFO"
    assert parsed_line["context"]["api_key"] == "[REDACTED]"
    assert parsed_line["context"]["request_id"] == "req-1"
