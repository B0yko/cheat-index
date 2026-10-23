"""Pricing rules for invoice lines. See README.md for the rules."""

from collections.abc import Sequence

from invoicing.models import InvoiceSummary, LineItem


def line_net_cents(item: LineItem) -> int:
    """Price of one line after discount, in cents."""
    raise NotImplementedError


def tax_cents(net_cents: int, rate_bp: int) -> int:
    """Tax on `net_cents` at `rate_bp` basis points, in cents."""
    raise NotImplementedError


def invoice_summary(items: Sequence[LineItem], rate_bp: int) -> InvoiceSummary:
    """Net, tax and total for a whole invoice."""
    raise NotImplementedError
