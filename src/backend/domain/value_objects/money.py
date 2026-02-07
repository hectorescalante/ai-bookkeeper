"""Money value object for representing monetary amounts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Self


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable value object representing a monetary amount in EUR.

    All amounts in AI Bookkeeper are in EUR.
    """

    amount: Decimal

    def __post_init__(self) -> None:
        """Validate and normalize the amount."""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        # Round to 2 decimal places
        rounded = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", rounded)

    @classmethod
    def zero(cls) -> Self:
        """Create a Money instance with zero amount."""
        return cls(Decimal("0.00"))

    @classmethod
    def from_float(cls, value: float) -> Self:
        """Create Money from a float value."""
        return cls(Decimal(str(value)))

    @classmethod
    def from_cents(cls, cents: int) -> Self:
        """Create Money from cents (integer)."""
        return cls(Decimal(cents) / 100)

    def __add__(self, other: Money) -> Money:
        """Add two Money amounts."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money and {type(other).__name__}")
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        """Subtract two Money amounts."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract {type(other).__name__} from Money")
        return Money(self.amount - other.amount)

    def __mul__(self, factor: Decimal | float | int) -> Money:
        """Multiply Money by a factor."""
        if isinstance(factor, (int, float)):
            factor = Decimal(str(factor))
        return Money(self.amount * factor)

    def __rmul__(self, factor: Decimal | float | int) -> Money:
        """Right multiply Money by a factor."""
        return self.__mul__(factor)

    def __neg__(self) -> Money:
        """Negate the amount."""
        return Money(-self.amount)

    def __abs__(self) -> Money:
        """Return absolute value."""
        return Money(abs(self.amount))

    def __lt__(self, other: Money) -> bool:
        """Compare Money amounts."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money and {type(other).__name__}")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        """Compare Money amounts."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money and {type(other).__name__}")
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        """Compare Money amounts."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money and {type(other).__name__}")
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        """Compare Money amounts."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money and {type(other).__name__}")
        return self.amount >= other.amount

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == Decimal("0.00")

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < 0

    def as_float(self) -> float:
        """Convert to float for serialization."""
        return float(self.amount)

    def __str__(self) -> str:
        """Format as string with EUR symbol."""
        return f"€{self.amount:,.2f}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Money({self.amount})"
