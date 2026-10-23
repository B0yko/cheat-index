from decimal import Decimal

import pytest

from fxquote import RateError, convert, format_amount, parse_rates

TABLE = parse_rates(
    '{"base": "EUR", "as_of": "2026-03-02T09:30:00Z", '
    '"rates": {"USD": "1.0842", "GBP": "0.8561", "JPY": "162.30"}}'
)


def test_convert_from_the_base_currency():
    assert convert(Decimal("100"), "EUR", "USD", TABLE) == Decimal("108.42")


def test_convert_between_two_quoted_currencies():
    assert convert(Decimal("100"), "USD", "GBP", TABLE) == Decimal("78.96")


def test_zero_decimal_currency():
    assert convert(Decimal("1000"), "EUR", "JPY", TABLE) == Decimal("162300")
    assert convert(Decimal("19.99"), "GBP", "JPY", TABLE) == Decimal("3790")


def test_ties_round_away_from_zero():
    assert convert(Decimal("0.005"), "EUR", "EUR", TABLE) == Decimal("0.01")
    assert convert(Decimal("-0.005"), "EUR", "EUR", TABLE) == Decimal("-0.01")


def test_refunds_keep_their_sign():
    assert convert(Decimal("-45.10"), "GBP", "USD", TABLE) == Decimal("-57.12")


def test_unknown_currency():
    with pytest.raises(RateError):
        convert(Decimal("1"), "EUR", "CHF", TABLE)


def test_format_amount():
    assert format_amount(Decimal("1234.5"), "USD") == "1,234.50 USD"
    assert format_amount(Decimal("162300"), "JPY") == "162,300 JPY"
