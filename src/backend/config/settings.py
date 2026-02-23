"""Application settings using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AI Bookkeeper"
    app_env: Literal["development", "production", "test"] = "development"
    debug: bool = False

    # API Server
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Database
    database_url: str = "sqlite:///data/ai_bookkeeper.db"

    # Gemini API (optional - can be configured via UI)
    gemini_api_key: str | None = None

    # Azure AD (for Outlook integration)
    azure_client_id: str | None = None
    azure_tenant_id: str = "common"
    azure_redirect_uri: str = "http://localhost:8000/api/settings/outlook/callback"

    # File Storage
    storage_path: Path = Path.home() / "Library" / "Application Support" / "AIBookkeeper"
    icloud_enabled: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "text"

    @property
    def data_path(self) -> Path:
        """Get the data directory path."""
        return self.storage_path / "data"

    @property
    def logs_path(self) -> Path:
        """Get the logs directory path."""
        return self.storage_path / "logs"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
