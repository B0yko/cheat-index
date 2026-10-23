import pytest

from cart import Line, Totals, price_cart


def amounts(totals: Totals) -> tuple[int, int, int]:
    return totals.subtotal, totals.discount, totals.total


def test_empty_cart():
    assert amounts(price_cart([])) == (0, 0, 0)


def test_subtotal_without_discounts():
    lines = [Line("mug", 1250, 2), Line("tea", 480, 3)]
    assert amounts(price_cart(lines)) == (3940, 0, 3940)


def test_bulk_discount_applies_to_big_lines_only():
    lines = [Line("pen", 150, 10), Line("pad", 300, 9)]
    # the pen line is 1500 cents and gets 150 off; the pad line is 2700 cents and gets nothing
    assert amounts(price_cart(lines)) == (4200, 150, 4050)


def test_percent_coupon_comes_after_bulk_discount():
    lines = [Line("pen", 200, 10), Line("cap", 1000, 1)]
    # subtotal 3000, bulk discount 200, 25% of the remaining 2800 is 700
    assert amounts(price_cart(lines, "PERCENT:25")) == (3000, 900, 2100)


def test_fixed_coupon_cannot_go_below_zero():
    assert amounts(price_cart([Line("pin", 300, 2)], "FIXED:1000")) == (600, 600, 0)


def test_percent_rounds_half_up():
    assert amounts(price_cart([Line("card", 1005, 1)], "PERCENT:10")) == (1005, 101, 904)


def test_unknown_coupon_is_rejected():
    with pytest.raises(ValueError):
        price_cart([Line("pin", 300, 2)], "HALF-OFF")
