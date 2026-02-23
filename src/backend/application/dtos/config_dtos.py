"""DTOs for configuration use cases."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class ConfigureCompanyRequest:
    """Request to configure company information."""

    name: str
    nif: str
    commission_rate: Decimal = Decimal("0.50")


@dataclass(frozen=True)
class CompanyResponse:
    """Response with company configuration."""

    id: UUID
    name: str
    nif: str
    commission_rate: Decimal
    is_configured: bool


@dataclass(frozen=True)
class ConfigureSettingsRequest:
    """Request to configure application settings."""

    gemini_api_key: str | None = None
    default_export_path: str | None = None
    extraction_prompt: str | None = None


@dataclass(frozen=True)
class SettingsResponse:
    """Response with application settings."""

    id: UUID
    has_api_key: bool
    outlook_configured: bool
    default_export_path: str
    extraction_prompt: str
