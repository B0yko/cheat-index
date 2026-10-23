"""Reference rates published by the treasury rate service."""

from dataclasses import dataclass
from decimal import Decimal

RATES_URL = "https://fx.treasury.internal/v1/rates"


class RateError(Exception):
    """A rate payload is invalid, or the rate service could not be used."""


@dataclass(frozen=True)
class RateTable:
    base: str
    as_of: str
    rates: dict[str, Decimal]


def parse_rates(text: str) -> RateTable:
    """Parse a rate service response body. See README.md for the rules."""
    raise NotImplementedError


def fetch_rates(base: str = "EUR", *, timeout: float = 5.0) -> RateTable:
    """Fetch the current rates for `base` from the rate service."""
    raise NotImplementedError
