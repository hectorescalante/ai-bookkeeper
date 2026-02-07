"""Invoice classification service."""

from backend.domain.entities import normalize_nif
from backend.domain.enums import DocumentType


class InvoiceClassifier:
    """Service to classify invoices based on NIF comparison.

    Classification logic:
    - If company NIF == issuer NIF → Client Invoice (revenue)
    - If company NIF == recipient NIF → Provider Invoice (cost)
    """

    def __init__(self, company_nif: str) -> None:
        """Initialize classifier with company NIF.

        Args:
            company_nif: The company's tax ID (NIF)

        Raises:
            ValueError: If company NIF is empty
        """
        normalized = normalize_nif(company_nif)
        if not normalized:
            raise ValueError("Company NIF is required for invoice classification")
        self._company_nif = normalized

    def classify(self, issuer_nif: str, recipient_nif: str) -> DocumentType:
        """Classify invoice based on issuer and recipient NIFs.

        Args:
            issuer_nif: NIF of the invoice issuer
            recipient_nif: NIF of the invoice recipient

        Returns:
            DocumentType indicating invoice classification

        Raises:
            ValueError: If classification cannot be determined
        """
        issuer_normalized = normalize_nif(issuer_nif)
        recipient_normalized = normalize_nif(recipient_nif)

        # Company is issuer → Client Invoice (we're billing them)
        if issuer_normalized == self._company_nif:
            return DocumentType.CLIENT_INVOICE

        # Company is recipient → Provider Invoice (they're billing us)
        if recipient_normalized == self._company_nif:
            return DocumentType.PROVIDER_INVOICE

        # Neither matches - this shouldn't happen for valid invoices
        raise ValueError(
            f"Cannot classify invoice: company NIF {self._company_nif} "
            f"matches neither issuer ({issuer_normalized}) nor recipient ({recipient_normalized})"
        )

    def is_revenue(self, issuer_nif: str, recipient_nif: str) -> bool:
        """Check if invoice represents revenue (client invoice)."""
        return self.classify(issuer_nif, recipient_nif) == DocumentType.CLIENT_INVOICE

    def is_cost(self, issuer_nif: str, recipient_nif: str) -> bool:
        """Check if invoice represents cost (provider invoice)."""
        return self.classify(issuer_nif, recipient_nif) == DocumentType.PROVIDER_INVOICE
