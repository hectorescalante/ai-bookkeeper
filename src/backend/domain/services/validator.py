"""Invoice data validation service."""

from dataclasses import dataclass

from backend.domain.value_objects import Money


@dataclass
class ValidationResult:
    """Result of invoice validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    @classmethod
    def success(cls, warnings: list[str] | None = None) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, errors=[], warnings=warnings or [])

    @classmethod
    def failure(cls, errors: list[str], warnings: list[str] | None = None) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(is_valid=False, errors=errors, warnings=warnings or [])


class InvoiceValidator:
    """Service to validate extracted invoice data completeness."""

    def validate_invoice_data(
        self,
        invoice_number: str | None,
        issuer_nif: str | None,
        recipient_nif: str | None,
        total_amount: Money | None,
        bl_references: list[str] | None,
        currency: str | None = "EUR",
    ) -> ValidationResult:
        """Validate extracted invoice data.

        Args:
            invoice_number: Invoice number
            issuer_nif: Issuer's tax ID
            recipient_nif: Recipient's tax ID
            total_amount: Invoice total
            bl_references: BL references found
            currency: Currency code (only EUR supported)

        Returns:
            ValidationResult with errors and warnings
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Required fields
        if not invoice_number:
            errors.append("Invoice number is required")

        if not issuer_nif:
            errors.append("Issuer NIF is required")

        if not recipient_nif:
            errors.append("Recipient NIF is required")

        if total_amount is None:
            errors.append("Total amount is required")
        elif total_amount.is_zero():
            warnings.append("Total amount is zero")
        elif total_amount.is_negative():
            warnings.append("Total amount is negative")

        # BL references
        if not bl_references:
            warnings.append("No BL references found - will need manual entry")
        elif len(bl_references) > 1:
            warnings.append(f"Multiple BL references found: {', '.join(bl_references)}")

        # Currency validation
        if currency and currency.upper() != "EUR":
            errors.append(f"Only EUR currency is supported, found: {currency}")

        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult.success(warnings)

    def validate_charges(
        self,
        charges_total: Money,
        invoice_total: Money,
        tolerance: Money | None = None,
    ) -> ValidationResult:
        """Validate that charges sum matches invoice total.

        Args:
            charges_total: Sum of all charge amounts
            invoice_total: Total from invoice header
            tolerance: Allowed difference (default €0.05 for rounding)

        Returns:
            ValidationResult
        """
        if tolerance is None:
            tolerance = Money.from_float(0.05)

        difference = abs(charges_total - invoice_total)

        if difference > tolerance:
            return ValidationResult.failure(
                errors=[
                    f"Charges total ({charges_total}) does not match "
                    f"invoice total ({invoice_total}). Difference: {difference}"
                ]
            )

        if not difference.is_zero():
            return ValidationResult.success(
                warnings=[
                    f"Minor rounding difference: charges={charges_total}, "
                    f"invoice={invoice_total}, diff={difference}"
                ]
            )

        return ValidationResult.success()
