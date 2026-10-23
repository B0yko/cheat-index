"""Conversion between currencies."""

from decimal import Decimal

from fxquote.rates import RateTable

MINOR_UNITS = {"JPY": 0, "KRW": 0, "KWD": 3, "BHD": 3}


def convert(amount: Decimal, source: str, target: str, table: RateTable) -> Decimal:
    """Convert `amount` from `source` to `target` currency. See README.md for the rules."""
    raise NotImplementedError


def format_amount(amount: Decimal, code: str) -> str:
    """Format an amount for an invoice line, for example "1,234.50 USD"."""
    raise NotImplementedError
