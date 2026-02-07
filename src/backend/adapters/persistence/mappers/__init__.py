"""Mappers for converting between domain entities and ORM models."""

from backend.adapters.persistence.mappers.booking_mapper import (
    booking_to_model,
    model_to_booking,
    set_booking_client_from_data,
)
from backend.adapters.persistence.mappers.config_mapper import (
    agent_to_model,
    company_to_model,
    model_to_agent,
    model_to_company,
    model_to_settings,
    settings_to_model,
)
from backend.adapters.persistence.mappers.document_mapper import (
    document_to_model,
    model_to_document,
)
from backend.adapters.persistence.mappers.invoice_mapper import (
    client_invoice_to_model,
    model_to_client_invoice,
    model_to_provider_invoice,
    provider_invoice_to_model,
)
from backend.adapters.persistence.mappers.party_mapper import (
    client_to_model,
    model_to_client,
    model_to_provider,
    provider_to_model,
)

__all__ = [
    # Booking mappers
    "booking_to_model",
    "model_to_booking",
    "set_booking_client_from_data",
    # Config mappers
    "agent_to_model",
    "company_to_model",
    "model_to_agent",
    "model_to_company",
    "model_to_settings",
    "settings_to_model",
    # Document mappers
    "document_to_model",
    "model_to_document",
    # Invoice mappers
    "client_invoice_to_model",
    "model_to_client_invoice",
    "model_to_provider_invoice",
    "provider_invoice_to_model",
    # Party mappers
    "client_to_model",
    "model_to_client",
    "model_to_provider",
    "provider_to_model",
]
