"""Quotes from the freight rate service."""

from dataclasses import dataclass
from decimal import Decimal


class QuoteError(Exception):
    """A quote is invalid or cannot be chosen."""


@dataclass(frozen=True)
class Quote:
    carrier: str
    base_amount: Decimal
    currency: str
    transit_days: int
    fuel_surcharge_pct: Decimal = Decimal(0)

    @property
    def total(self) -> Decimal:
        """Base amount plus fuel surcharge, rounded half up to cents."""
        raise NotImplementedError


def parse_quote(body: str) -> Quote:
    """Parse a rate service answer. See README.md for the rules."""
    raise NotImplementedError


def pick_best(quotes: list[Quote], *, max_transit_days: int | None = None) -> Quote:
    """The cheapest quote, optionally within a transit time limit."""
    raise NotImplementedError
