from decimal import Decimal

import pytest

from fxquote import RateError, fetch_rates, parse_rates

SAMPLE = (
    '{"base": "EUR", "as_of": "2026-03-02T09:30:00Z", '
    '"rates": {"USD": "1.0842", "GBP": "0.8561", "JPY": "162.30"}}'
)


def test_parse_reads_rates_as_decimals():
    table = parse_rates(SAMPLE)
    assert table.base == "EUR"
    assert table.as_of == "2026-03-02T09:30:00Z"
    assert table.rates["USD"] == Decimal("1.0842")
    assert table.rates["JPY"] == Decimal("162.30")


def test_base_currency_is_always_present():
    assert parse_rates(SAMPLE).rates["EUR"] == Decimal(1)


def test_rate_listed_for_the_base_is_ignored():
    text = '{"base": "EUR", "as_of": "x", "rates": {"EUR": "2", "USD": "1.1"}}'
    assert parse_rates(text).rates["EUR"] == Decimal(1)


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        "[]",
        '{"as_of": "x", "rates": {}}',
        '{"base": "EUR", "rates": {"USD": "1.1"}}',
        '{"base": "EUR", "as_of": "x"}',
        '{"base": "EUR", "as_of": "x", "rates": {"usd": "1.1"}}',
        '{"base": "EUR", "as_of": "x", "rates": {"USD": "0"}}',
        '{"base": "EUR", "as_of": "x", "rates": {"USD": "-1.2"}}',
        '{"base": "EUR", "as_of": "x", "rates": {"USD": "abc"}}',
    ],
)
def test_parse_rejects_bad_payloads(text):
    with pytest.raises(RateError):
        parse_rates(text)


def test_fetch_rejects_a_malformed_base_before_any_request():
    with pytest.raises(RateError):
        fetch_rates("euro")


def test_live_rates_cover_the_major_currencies():
    # talks to the real rate service
    table = fetch_rates("EUR")
    assert table.base == "EUR"
    assert {"USD", "GBP", "JPY"} <= set(table.rates)
