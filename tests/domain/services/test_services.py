"""Tests for domain services."""

from decimal import Decimal

import pytest

from backend.domain.enums import DocumentType
from backend.domain.services import (
    DuplicateChecker,
    InvoiceClassifier,
    InvoiceValidator,
    TaxAllocator,
)
from backend.domain.value_objects import FileHash, Money


class TestInvoiceClassifier:
    """Tests for InvoiceClassifier service."""

    def test_init_requires_company_nif(self) -> None:
        """Test that classifier requires non-empty company NIF."""
        with pytest.raises(ValueError, match="Company NIF is required"):
            InvoiceClassifier("")

    def test_init_normalizes_nif(self) -> None:
        """Test that classifier normalizes the company NIF."""
        classifier = InvoiceClassifier("A-12.345 678")
        assert classifier._company_nif == "A12345678"

    def test_classify_client_invoice(self) -> None:
        """Test classifying invoice where company is issuer (client invoice)."""
        classifier = InvoiceClassifier("A12345678")
        result = classifier.classify(
            issuer_nif="A12345678",  # Company
            recipient_nif="B87654321",  # Client
        )
        assert result == DocumentType.CLIENT_INVOICE

    def test_classify_provider_invoice(self) -> None:
        """Test classifying invoice where company is recipient (provider invoice)."""
        classifier = InvoiceClassifier("A12345678")
        result = classifier.classify(
            issuer_nif="B87654321",  # Provider
            recipient_nif="A12345678",  # Company
        )
        assert result == DocumentType.PROVIDER_INVOICE

    def test_classify_normalizes_input_nifs(self) -> None:
        """Test that classification normalizes input NIFs."""
        classifier = InvoiceClassifier("A12345678")
        result = classifier.classify(
            issuer_nif="a-12.345 678",  # Company (different format)
            recipient_nif="B87654321",
        )
        assert result == DocumentType.CLIENT_INVOICE

    def test_classify_neither_matches(self) -> None:
        """Test classification fails when company is neither issuer nor recipient."""
        classifier = InvoiceClassifier("A12345678")
        with pytest.raises(ValueError, match="Cannot classify invoice"):
            classifier.classify(
                issuer_nif="B11111111",
                recipient_nif="B22222222",
            )

    def test_is_revenue(self) -> None:
        """Test is_revenue helper method."""
        classifier = InvoiceClassifier("A12345678")
        assert classifier.is_revenue("A12345678", "B87654321")
        assert not classifier.is_revenue("B87654321", "A12345678")

    def test_is_cost(self) -> None:
        """Test is_cost helper method."""
        classifier = InvoiceClassifier("A12345678")
        assert classifier.is_cost("B87654321", "A12345678")
        assert not classifier.is_cost("A12345678", "B87654321")


class TestDuplicateChecker:
    """Tests for DuplicateChecker service."""

    def test_empty_checker(self) -> None:
        """Test checker with no known hashes."""
        checker = DuplicateChecker()
        file_hash = FileHash.sha256("abc123")
        assert not checker.is_duplicate(file_hash)

    def test_is_duplicate_with_known_hash(self) -> None:
        """Test detecting duplicate."""
        checker = DuplicateChecker(known_hashes={"abc123"})
        file_hash = FileHash.sha256("abc123")
        assert checker.is_duplicate(file_hash)

    def test_is_not_duplicate(self) -> None:
        """Test non-duplicate hash."""
        checker = DuplicateChecker(known_hashes={"abc123"})
        file_hash = FileHash.sha256("xyz789")
        assert not checker.is_duplicate(file_hash)

    def test_add_hash(self) -> None:
        """Test adding a hash."""
        checker = DuplicateChecker()
        file_hash = FileHash.sha256("abc123")

        assert not checker.is_duplicate(file_hash)
        checker.add_hash(file_hash)
        assert checker.is_duplicate(file_hash)

    def test_remove_hash(self) -> None:
        """Test removing a hash."""
        checker = DuplicateChecker(known_hashes={"abc123"})
        file_hash = FileHash.sha256("abc123")

        assert checker.is_duplicate(file_hash)
        checker.remove_hash(file_hash)
        assert not checker.is_duplicate(file_hash)


class TestInvoiceValidator:
    """Tests for InvoiceValidator service."""

    def test_valid_invoice(self) -> None:
        """Test validating a complete invoice."""
        validator = InvoiceValidator()
        result = validator.validate_invoice_data(
            invoice_number="INV-001",
            issuer_nif="A12345678",
            recipient_nif="B87654321",
            total_amount=Money.from_float(1000.00),
            bl_references=["BL-001"],
            currency="EUR",
        )
        assert result.is_valid
        assert not result.errors

    def test_missing_invoice_number(self) -> None:
        """Test validation fails for missing invoice number."""
        validator = InvoiceValidator()
        result = validator.validate_invoice_data(
            invoice_number=None,
            issuer_nif="A12345678",
            recipient_nif="B87654321",
            total_amount=Money.from_float(1000.00),
            bl_references=["BL-001"],
        )
        assert not result.is_valid
        assert "Invoice number is required" in result.errors

    def test_missing_nifs(self) -> None:
        """Test validation fails for missing NIFs."""
        validator = InvoiceValidator()
        result = validator.validate_invoice_data(
            invoice_number="INV-001",
            issuer_nif=None,
            recipient_nif=None,
            total_amount=Money.from_float(1000.00),
            bl_references=["BL-001"],
        )
        assert not result.is_valid
        assert "Issuer NIF is required" in result.errors
        assert "Recipient NIF is required" in result.errors

    def test_missing_total_amount(self) -> None:
        """Test validation fails for missing total."""
        validator = InvoiceValidator()
        result = validator.validate_invoice_data(
            invoice_number="INV-001",
            issuer_nif="A12345678",
            recipient_nif="B87654321",
            total_amount=None,
            bl_references=["BL-001"],
        )
        assert not result.is_valid
        assert "Total amount is required" in result.errors

    def test_zero_amount_warning(self) -> None:
        """Test warning for zero amount."""
        validator = InvoiceValidator()
        result = validator.validate_invoice_data(
            invoice_number="INV-001",
            issuer_nif="A12345678",
            recipient_nif="B87654321",
            total_amount=Money.zero(),
            bl_references=["BL-001"],
        )
        assert result.is_valid
        assert "Total amount is zero" in result.warnings

    def test_no_bl_references_warning(self) -> None:
        """Test warning for no BL references."""
        validator = InvoiceValidator()
        result = validator.validate_invoice_data(
            invoice_number="INV-001",
            issuer_nif="A12345678",
            recipient_nif="B87654321",
            total_amount=Money.from_float(1000.00),
            bl_references=None,
        )
        assert result.is_valid
        assert "No BL references found" in result.warnings[0]

    def test_multiple_bl_references_warning(self) -> None:
        """Test warning for multiple BL references."""
        validator = InvoiceValidator()
        result = validator.validate_invoice_data(
            invoice_number="INV-001",
            issuer_nif="A12345678",
            recipient_nif="B87654321",
            total_amount=Money.from_float(1000.00),
            bl_references=["BL-001", "BL-002"],
        )
        assert result.is_valid
        assert "Multiple BL references" in result.warnings[0]

    def test_invalid_currency(self) -> None:
        """Test validation fails for non-EUR currency."""
        validator = InvoiceValidator()
        result = validator.validate_invoice_data(
            invoice_number="INV-001",
            issuer_nif="A12345678",
            recipient_nif="B87654321",
            total_amount=Money.from_float(1000.00),
            bl_references=["BL-001"],
            currency="USD",
        )
        assert not result.is_valid
        assert "Only EUR currency is supported" in result.errors[0]

    def test_validate_charges_match(self) -> None:
        """Test charges validation when totals match."""
        validator = InvoiceValidator()
        result = validator.validate_charges(
            charges_total=Money.from_float(1000.00),
            invoice_total=Money.from_float(1000.00),
        )
        assert result.is_valid
        assert not result.warnings

    def test_validate_charges_minor_difference(self) -> None:
        """Test charges validation with minor rounding difference."""
        validator = InvoiceValidator()
        result = validator.validate_charges(
            charges_total=Money.from_float(1000.01),
            invoice_total=Money.from_float(1000.00),
        )
        assert result.is_valid
        assert "Minor rounding difference" in result.warnings[0]

    def test_validate_charges_significant_difference(self) -> None:
        """Test charges validation fails with significant difference."""
        validator = InvoiceValidator()
        result = validator.validate_charges(
            charges_total=Money.from_float(1000.00),
            invoice_total=Money.from_float(1100.00),
        )
        assert not result.is_valid
        assert "does not match" in result.errors[0]


class TestTaxAllocator:
    """Tests for TaxAllocator service."""

    def test_single_booking_allocation(self) -> None:
        """Test tax allocation for single booking."""
        allocator = TaxAllocator()
        allocations = allocator.allocate_tax(
            booking_amounts={"BL-001": Money.from_float(1000.00)},
            total_tax=Money.from_float(210.00),
        )

        assert len(allocations) == 1
        assert allocations[0].bl_reference == "BL-001"
        assert allocations[0].base_amount == Money.from_float(1000.00)
        assert allocations[0].tax_amount == Money.from_float(210.00)
        assert allocations[0].percentage == Decimal("100.00")

    def test_two_booking_allocation_60_40(self) -> None:
        """Test tax allocation for two bookings (60/40 split)."""
        allocator = TaxAllocator()
        allocations = allocator.allocate_tax(
            booking_amounts={
                "BL-001": Money.from_float(600.00),
                "BL-002": Money.from_float(400.00),
            },
            total_tax=Money.from_float(210.00),
        )

        assert len(allocations) == 2

        # BL-001 gets 60%
        bl001 = next(a for a in allocations if a.bl_reference == "BL-001")
        assert bl001.base_amount == Money.from_float(600.00)
        assert bl001.tax_amount == Money.from_float(126.00)
        assert bl001.percentage == Decimal("60.00")

        # BL-002 gets 40%
        bl002 = next(a for a in allocations if a.bl_reference == "BL-002")
        assert bl002.base_amount == Money.from_float(400.00)
        assert bl002.tax_amount == Money.from_float(84.00)
        assert bl002.percentage == Decimal("40.00")

    def test_allocation_sums_to_total(self) -> None:
        """Test that allocated tax sums to total tax."""
        allocator = TaxAllocator()
        allocations = allocator.allocate_tax(
            booking_amounts={
                "BL-001": Money.from_float(333.33),
                "BL-002": Money.from_float(333.33),
                "BL-003": Money.from_float(333.34),
            },
            total_tax=Money.from_float(100.00),
        )

        total_allocated = sum((a.tax_amount for a in allocations), Money.zero())
        assert total_allocated == Money.from_float(100.00)

    def test_empty_bookings_raises_error(self) -> None:
        """Test that empty bookings raises error."""
        allocator = TaxAllocator()
        with pytest.raises(ValueError, match="At least one booking"):
            allocator.allocate_tax(
                booking_amounts={},
                total_tax=Money.from_float(100.00),
            )

    def test_zero_charges_raises_error(self) -> None:
        """Test that zero total charges raises error."""
        allocator = TaxAllocator()
        with pytest.raises(ValueError, match="cannot be zero"):
            allocator.allocate_tax(
                booking_amounts={"BL-001": Money.zero()},
                total_tax=Money.from_float(100.00),
            )

    def test_calculate_total_per_booking(self) -> None:
        """Test calculating total (charges + tax) per booking."""
        allocator = TaxAllocator()
        allocations = allocator.allocate_tax(
            booking_amounts={
                "BL-001": Money.from_float(600.00),
                "BL-002": Money.from_float(400.00),
            },
            total_tax=Money.from_float(210.00),
        )

        totals = allocator.calculate_total_per_booking(allocations)

        assert totals["BL-001"] == Money.from_float(726.00)  # 600 + 126
        assert totals["BL-002"] == Money.from_float(484.00)  # 400 + 84
