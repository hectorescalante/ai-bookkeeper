"""Centralized logging configuration and sanitization utilities."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from backend.config.settings import Settings

LOG_FILE_PREFIX = "app"
LOG_RETENTION_DAYS = 30
DEFAULT_LOG_LEVEL_DEVELOPMENT = "DEBUG"
DEFAULT_LOG_LEVEL_NON_DEVELOPMENT = "INFO"

_RUNTIME_LOGS_PATH = Path.home() / "Library" / "Logs" / "AIBookkeeper"
_REDACTED_VALUE = "[REDACTED]"
_LOGGING_CONFIGURED = False

_RESERVED_LOG_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__.keys())

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:api[_-]?key|token|secret|password|authorization|auth|refresh|access"
    r"|nif|email|phone|address|sender|subject|raw[_-]?json|invoice|charge|amount|total"
    r"|subtotal|tax)",
    re.IGNORECASE,
)
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"(?i)\bbearer\s+[a-z0-9\-._~+/]+=*\b"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+"),
)


def get_runtime_logs_path() -> Path:
    """Return the canonical runtime logs directory."""
    return _RUNTIME_LOGS_PATH


def setup_logging(
    settings: Settings,
    *,
    force_reconfigure: bool = False,
) -> None:
    """Configure root logging with JSON output and file retention."""
    global _LOGGING_CONFIGURED  # noqa: PLW0603

    if _LOGGING_CONFIGURED and not force_reconfigure:
        return

    log_level_name = _resolve_log_level(settings)
    log_level = getattr(logging, log_level_name, logging.INFO)

    log_directory = get_runtime_logs_path()
    log_directory.mkdir(parents=True, exist_ok=True)
    cleanup_old_logs(log_directory, retention_days=LOG_RETENTION_DAYS)

    log_file_path = log_directory / f"{LOG_FILE_PREFIX}-{date.today().isoformat()}.log"

    formatter = JsonLogFormatter()
    redaction_filter = RedactingLogFilter()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redaction_filter)

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redaction_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        named_logger = logging.getLogger(logger_name)
        named_logger.handlers.clear()
        named_logger.setLevel(log_level)
        named_logger.propagate = True

    _LOGGING_CONFIGURED = True


def cleanup_old_logs(log_directory: Path, *, retention_days: int) -> None:
    """Delete old daily log files from the log directory."""
    cutoff = datetime.now(tz=UTC) - timedelta(days=retention_days)

    for log_path in log_directory.glob(f"{LOG_FILE_PREFIX}-*.log"):
        try:
            modified_at = datetime.fromtimestamp(log_path.stat().st_mtime, tz=UTC)
            if modified_at < cutoff:
                log_path.unlink(missing_ok=True)
        except OSError:
            continue


def sanitize_for_logging(value: Any, *, key: str | None = None) -> Any:
    """Return a recursively sanitized copy safe for logs and diagnostics."""
    if key and _looks_sensitive_key(key):
        return _REDACTED_VALUE

    if isinstance(value, dict):
        return {
            nested_key: sanitize_for_logging(nested_value, key=nested_key)
            for nested_key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [sanitize_for_logging(item) for item in value]

    if isinstance(value, tuple):
        return tuple(sanitize_for_logging(item) for item in value)

    if isinstance(value, set):
        return [sanitize_for_logging(item) for item in value]

    if isinstance(value, str):
        return sanitize_text(value)

    return value


def sanitize_text(value: str) -> str:
    """Sanitize potentially sensitive patterns from free-form text."""
    sanitized = value
    for pattern in _SENSITIVE_VALUE_PATTERNS:
        sanitized = pattern.sub(_REDACTED_VALUE, sanitized)
    return sanitized


def sanitize_log_line(line: str) -> str:
    """Sanitize a single log line preserving JSON structure when possible."""
    stripped = line.strip()
    if not stripped:
        return stripped

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return sanitize_text(stripped)

    sanitized = sanitize_for_logging(parsed)
    return json.dumps(sanitized, ensure_ascii=False)


class RedactingLogFilter(logging.Filter):
    """Filter that sanitizes extras and formatted messages before emission."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_text(record.msg)

        if record.args:
            record.args = tuple(sanitize_for_logging(arg) for arg in record.args)

        for key, value in list(record.__dict__.items()):
            if key in _RESERVED_LOG_RECORD_FIELDS or key.startswith("_"):
                continue
            record.__dict__[key] = sanitize_for_logging(value, key=key)

        return True


class JsonLogFormatter(logging.Formatter):
    """Formatter that emits structured JSON payloads."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _to_timestamp(record.created),
            "level": record.levelname,
            "component": record.name,
            "message": sanitize_text(record.getMessage()),
            "context": _extract_context(record),
        }

        if record.exc_info:
            payload["context"]["exception"] = sanitize_text(
                self.formatException(record.exc_info)
            )

        return json.dumps(payload, ensure_ascii=False, default=_json_default)


def _extract_context(record: logging.LogRecord) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key, value in record.__dict__.items():
        if key in _RESERVED_LOG_RECORD_FIELDS or key.startswith("_"):
            continue
        context[key] = sanitize_for_logging(value, key=key)
    return context


def _looks_sensitive_key(key: str) -> bool:
    return bool(_SENSITIVE_KEY_PATTERN.search(key))


def _resolve_log_level(settings: Settings) -> str:
    if settings.app_env == "development" and settings.log_level.upper() == "INFO":
        return DEFAULT_LOG_LEVEL_DEVELOPMENT
    if settings.app_env == "test":
        return settings.log_level.upper()
    if settings.log_level:
        return settings.log_level.upper()
    return DEFAULT_LOG_LEVEL_NON_DEVELOPMENT


def _to_timestamp(created_at: float) -> str:
    dt = datetime.fromtimestamp(created_at, tz=UTC)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return repr(value)
