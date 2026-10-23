"""Plain data types used by the pricing code."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Line:
    """One cart line: a product, its unit price in cents and how many were ordered."""

    sku: str
    unit_cents: int
    qty: int


@dataclass(frozen=True)
class Totals:
    """Result of pricing a cart. All amounts are whole cents."""

    subtotal: int
    discount: int
    total: int
