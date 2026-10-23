"""Plain data types shared by the pricing functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LineItem:
    """One invoice line. Prices are in cents, the discount is a whole percentage."""

    sku: str
    unit_price_cents: int
    quantity: int
    discount_percent: int = 0


@dataclass(frozen=True)
class InvoiceSummary:
    net_cents: int
    tax_cents: int
    total_cents: int
