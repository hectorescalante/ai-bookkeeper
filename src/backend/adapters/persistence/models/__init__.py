"""SQLAlchemy ORM models for all entities.

Import all models here for Alembic autogenerate to detect them.
"""

from backend.adapters.persistence.models.booking import BookingModel
from backend.adapters.persistence.models.configuration import (
    AgentModel,
    CompanyModel,
    SettingsModel,
)
from backend.adapters.persistence.models.document import DocumentModel
from backend.adapters.persistence.models.invoice import ClientInvoiceModel, ProviderInvoiceModel
from backend.adapters.persistence.models.party import ClientModel, ProviderModel

__all__ = [
    "AgentModel",
    "BookingModel",
    "ClientInvoiceModel",
    "ClientModel",
    "CompanyModel",
    "DocumentModel",
    "ProviderInvoiceModel",
    "ProviderModel",
    "SettingsModel",
]
