"""Cart pricing."""

from cart.models import Line, Totals


def price_cart(lines: list[Line], coupon: str | None = None) -> Totals:
    """Price a cart. See README.md for the discount rules."""
    raise NotImplementedError
