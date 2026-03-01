"""Configuration entities (singletons)."""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from backend.domain.entities.party import normalize_nif

# Default extraction prompt (can be loaded from docs/extraction-prompt.md)
DEFAULT_EXTRACTION_PROMPT = """Extract invoice data from the following PDF document.
Return a JSON object with the extracted information."""

# Default AI model identifier
DEFAULT_AI_MODEL = "gemini-3-pro"


@dataclass
class Company:
    """Company configuration (singleton).

    The company's NIF is used to classify invoices:
    - Issuer NIF = Company NIF → Revenue (Client Invoice)
    - Recipient NIF = Company NIF → Cost (Provider Invoice)
    """

    id: UUID
    name: str
    nif: str  # Tax ID, used for invoice classification
    address: str = ""
    contact_info: str = ""
    agent_commission_rate: Decimal = Decimal("0.50")  # Default 50%

    @classmethod
    def create(
        cls,
        name: str = "",
        nif: str = "",
        address: str = "",
        contact_info: str = "",
        commission_rate: Decimal = Decimal("0.50"),
    ) -> "Company":
        """Create company configuration."""
        return cls(
            id=uuid4(),
            name=name,
            nif=normalize_nif(nif) if nif else "",
            address=address,
            contact_info=contact_info,
            agent_commission_rate=commission_rate,
        )

    def update(
        self,
        name: str | None = None,
        nif: str | None = None,
        address: str | None = None,
        contact_info: str | None = None,
        commission_rate: Decimal | None = None,
    ) -> None:
        """Update company settings."""
        if name is not None:
            self.name = name
        if nif is not None:
            self.nif = normalize_nif(nif)
        if address is not None:
            self.address = address
        if contact_info is not None:
            self.contact_info = contact_info
        if commission_rate is not None:
            self.agent_commission_rate = commission_rate

    @property
    def is_configured(self) -> bool:
        """Check if company NIF is configured (required for invoice processing)."""
        return bool(self.nif)


@dataclass
class Agent:
    """Agent profile (singleton)."""

    id: UUID
    name: str = ""
    email: str = ""
    phone: str = ""

    @classmethod
    def create(
        cls,
        name: str = "",
        email: str = "",
        phone: str = "",
    ) -> "Agent":
        """Create agent profile."""
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            phone=phone,
        )

    def update(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> None:
        """Update agent profile."""
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone


@dataclass
class Settings:
    """Application settings (singleton)."""

    id: UUID
    gemini_api_key: str = ""
    outlook_configured: bool = False
    outlook_refresh_token: str = ""  # Encrypted, stored in keychain ideally
    default_export_path: str = ""
    extraction_prompt: str = field(default=DEFAULT_EXTRACTION_PROMPT)
    onboarding_dismissed: bool = False

    @classmethod
    def create(cls) -> "Settings":
        """Create default settings."""
        return cls(id=uuid4())

    def set_api_key(self, api_key: str) -> None:
        """Set Gemini API key."""
        self.gemini_api_key = api_key

    def clear_api_key(self) -> None:
        """Clear API key."""
        self.gemini_api_key = ""

    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.gemini_api_key)

    def set_outlook_configured(self, configured: bool, refresh_token: str = "") -> None:
        """Set Outlook connection status."""
        self.outlook_configured = configured
        self.outlook_refresh_token = refresh_token if configured else ""

    def disconnect_outlook(self) -> None:
        """Disconnect Outlook."""
        self.outlook_configured = False
        self.outlook_refresh_token = ""

    def update_extraction_prompt(self, prompt: str) -> None:
        """Update extraction prompt."""
        self.extraction_prompt = prompt

    def reset_extraction_prompt(self) -> None:
        """Reset extraction prompt to default."""
        self.extraction_prompt = DEFAULT_EXTRACTION_PROMPT

    def set_onboarding_dismissed(self, dismissed: bool) -> None:
        """Set onboarding guide dismissed state."""
        self.onboarding_dismissed = dismissed
