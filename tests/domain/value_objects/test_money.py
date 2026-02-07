"""Tests for Money value object."""

from decimal import Decimal

import pytest

from backend.domain.value_objects import Money


class TestMoneyCreation:
    """Tests for Money creation."""

    def test_create_from_decimal(self) -> None:
        """Test creating Money from Decimal."""
        money = Money(Decimal("100.50"))
        assert money.amount == Decimal("100.50")

    def test_create_from_int(self) -> None:
        """Test creating Money from int (via post_init conversion)."""
        money = Money(100)
        assert money.amount == Decimal("100.00")

    def test_create_from_float_class_method(self) -> None:
        """Test creating Money from float."""
        money = Money.from_float(100.50)
        assert money.amount == Decimal("100.50")

    def test_create_from_cents(self) -> None:
        """Test creating Money from cents."""
        money = Money.from_cents(10050)
        assert money.amount == Decimal("100.50")

    def test_create_zero(self) -> None:
        """Test creating zero Money."""
        money = Money.zero()
        assert money.amount == Decimal("0.00")
        assert money.is_zero()

    def test_rounds_to_two_decimal_places(self) -> None:
        """Test that Money rounds to 2 decimal places."""
        money = Money(Decimal("100.555"))
        assert money.amount == Decimal("100.56")  # Rounds up

        money2 = Money(Decimal("100.554"))
        assert money2.amount == Decimal("100.55")  # Rounds down


class TestMoneyArithmetic:
    """Tests for Money arithmetic operations."""

    def test_addition(self) -> None:
        """Test adding two Money amounts."""
        a = Money.from_float(100.00)
        b = Money.from_float(50.50)
        result = a + b
        assert result.amount == Decimal("150.50")

    def test_subtraction(self) -> None:
        """Test subtracting two Money amounts."""
        a = Money.from_float(100.00)
        b = Money.from_float(30.25)
        result = a - b
        assert result.amount == Decimal("69.75")

    def test_subtraction_negative_result(self) -> None:
        """Test subtraction resulting in negative amount."""
        a = Money.from_float(50.00)
        b = Money.from_float(100.00)
        result = a - b
        assert result.amount == Decimal("-50.00")
        assert result.is_negative()

    def test_multiplication_by_decimal(self) -> None:
        """Test multiplying Money by Decimal."""
        money = Money.from_float(100.00)
        result = money * Decimal("0.50")
        assert result.amount == Decimal("50.00")

    def test_multiplication_by_float(self) -> None:
        """Test multiplying Money by float."""
        money = Money.from_float(100.00)
        result = money * 0.5
        assert result.amount == Decimal("50.00")

    def test_multiplication_by_int(self) -> None:
        """Test multiplying Money by int."""
        money = Money.from_float(100.00)
        result = money * 2
        assert result.amount == Decimal("200.00")

    def test_right_multiplication(self) -> None:
        """Test right multiplication (factor * money)."""
        money = Money.from_float(100.00)
        result = 0.5 * money
        assert result.amount == Decimal("50.00")

    def test_negation(self) -> None:
        """Test negating Money."""
        money = Money.from_float(100.00)
        result = -money
        assert result.amount == Decimal("-100.00")

    def test_absolute_value(self) -> None:
        """Test absolute value of negative Money."""
        money = Money.from_float(-100.00)
        result = abs(money)
        assert result.amount == Decimal("100.00")

    def test_addition_type_error(self) -> None:
        """Test that adding non-Money raises TypeError."""
        money = Money.from_float(100.00)
        with pytest.raises(TypeError):
            _ = money + 50

    def test_subtraction_type_error(self) -> None:
        """Test that subtracting non-Money raises TypeError."""
        money = Money.from_float(100.00)
        with pytest.raises(TypeError):
            _ = money - 50


class TestMoneyComparison:
    """Tests for Money comparison operations."""

    def test_less_than(self) -> None:
        """Test less than comparison."""
        a = Money.from_float(50.00)
        b = Money.from_float(100.00)
        assert a < b
        assert not b < a

    def test_less_than_or_equal(self) -> None:
        """Test less than or equal comparison."""
        a = Money.from_float(50.00)
        b = Money.from_float(100.00)
        c = Money.from_float(50.00)
        assert a <= b
        assert a <= c
        assert not b <= a

    def test_greater_than(self) -> None:
        """Test greater than comparison."""
        a = Money.from_float(100.00)
        b = Money.from_float(50.00)
        assert a > b
        assert not b > a

    def test_greater_than_or_equal(self) -> None:
        """Test greater than or equal comparison."""
        a = Money.from_float(100.00)
        b = Money.from_float(50.00)
        c = Money.from_float(100.00)
        assert a >= b
        assert a >= c
        assert not b >= a

    def test_equality(self) -> None:
        """Test equality comparison."""
        a = Money.from_float(100.00)
        b = Money.from_float(100.00)
        c = Money.from_float(50.00)
        assert a == b
        assert a != c

    def test_comparison_type_error(self) -> None:
        """Test that comparing with non-Money raises TypeError."""
        money = Money.from_float(100.00)
        with pytest.raises(TypeError):
            _ = money < 50


class TestMoneyProperties:
    """Tests for Money properties and methods."""

    def test_is_zero(self) -> None:
        """Test is_zero check."""
        zero = Money.zero()
        non_zero = Money.from_float(1.00)
        assert zero.is_zero()
        assert not non_zero.is_zero()

    def test_is_positive(self) -> None:
        """Test is_positive check."""
        positive = Money.from_float(100.00)
        zero = Money.zero()
        negative = Money.from_float(-100.00)
        assert positive.is_positive()
        assert not zero.is_positive()
        assert not negative.is_positive()

    def test_is_negative(self) -> None:
        """Test is_negative check."""
        positive = Money.from_float(100.00)
        zero = Money.zero()
        negative = Money.from_float(-100.00)
        assert negative.is_negative()
        assert not zero.is_negative()
        assert not positive.is_negative()

    def test_as_float(self) -> None:
        """Test conversion to float."""
        money = Money.from_float(100.50)
        assert money.as_float() == 100.50

    def test_str_representation(self) -> None:
        """Test string representation."""
        money = Money.from_float(1234.56)
        assert str(money) == "€1,234.56"

    def test_repr(self) -> None:
        """Test repr."""
        money = Money.from_float(100.50)
        assert repr(money) == "Money(100.50)"


class TestMoneyImmutability:
    """Tests for Money immutability."""

    def test_is_frozen(self) -> None:
        """Test that Money is immutable."""
        money = Money.from_float(100.00)
        with pytest.raises(AttributeError):
            money.amount = Decimal("200.00")
