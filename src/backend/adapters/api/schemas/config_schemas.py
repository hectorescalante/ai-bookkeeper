"""Pydantic schemas for configuration API."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyRequest(BaseModel):
    """Request to configure company."""

    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    nif: str = Field(..., min_length=1, max_length=50, description="Tax ID (NIF)")
    address: str = Field("", max_length=500, description="Company address")
    contact_info: str = Field("", max_length=500, description="Company contact information")
    commission_rate: Decimal = Field(..., ge=0, le=1, description="Agent commission rate (0.0-1.0)")


class CompanyResponse(BaseModel):
    """Company configuration response."""

    id: UUID
    name: str
    nif: str
    address: str
    contact_info: str
    commission_rate: Decimal
    is_configured: bool

class AgentRequest(BaseModel):
    """Request to configure agent profile."""

    name: str = Field(..., min_length=1, max_length=200, description="Agent name")
    email: str = Field(..., min_length=1, max_length=255, description="Agent email")
    phone: str = Field(..., min_length=1, max_length=50, description="Agent phone")


class AgentResponse(BaseModel):
    """Agent profile response."""

    id: UUID
    name: str
    email: str
    phone: str


class SettingsRequest(BaseModel):
    """Request to configure settings."""

    gemini_api_key: str | None = Field(None, description="Google Gemini API key for AI extraction")
    default_export_path: str | None = Field(None, description="Default export path for reports")
    extraction_prompt: str | None = Field(None, description="AI extraction prompt")


class SettingsResponse(BaseModel):
    """Settings response."""

    id: UUID
    has_api_key: bool
    outlook_configured: bool
    default_export_path: str
    extraction_prompt: str


class TestGeminiConnectionRequest(BaseModel):
    """Request to test Gemini API connection."""

    gemini_api_key: str | None = Field(
        None,
        description="Gemini API key to test; if omitted, uses stored key",
    )


class TestGeminiConnectionResponse(BaseModel):
    """Response for Gemini API connection test."""

    valid: bool
    message: str
