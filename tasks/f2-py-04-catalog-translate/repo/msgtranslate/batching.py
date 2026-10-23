"""Batching of texts and cost estimates."""

from decimal import Decimal


def batch_texts(texts: list[str], *, max_items: int = 50, max_chars: int = 5000) -> list[list[str]]:
    """Split texts into ordered batches that respect the item and character limits."""
    raise NotImplementedError


def billable_characters(texts: list[str]) -> int:
    """Characters the API bills for: the texts without their placeholders."""
    raise NotImplementedError


def estimate_cost(texts: list[str], price_per_million: Decimal) -> Decimal:
    """Estimated price in the currency of `price_per_million`, rounded up to 4 decimals."""
    raise NotImplementedError
