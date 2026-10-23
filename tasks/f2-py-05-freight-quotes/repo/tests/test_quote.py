from decimal import Decimal

import pytest

from freight import Quote, QuoteError, parse_quote, pick_best

BODY = (
    '{"carrier": "Harborline", "price": {"amount": "137.50", "currency": "EUR"}, '
    '"transit_days": 2, "fuel_surcharge_pct": "6.5"}'
)


def quote(carrier, amount, days, pct="0", currency="EUR"):
    return Quote(carrier, Decimal(amount), currency, days, Decimal(pct))


def test_parse_quote():
    assert parse_quote(BODY) == Quote("Harborline", Decimal("137.50"), "EUR", 2, Decimal("6.5"))


def test_total_includes_surcharge_rounded_half_up():
    assert parse_quote(BODY).total == Decimal("146.44")
    assert quote("X", "10.00", 1, "0.05").total == Decimal("10.01")


def test_surcharge_is_optional_and_numbers_are_accepted():
    q = parse_quote('{"carrier": " Acme ", "price": {"amount": 80, "currency": "USD"}, "transit_days": 3}')
    assert q == Quote("Acme", Decimal("80"), "USD", 3, Decimal(0))
    assert q.total == Decimal("80.00")


@pytest.mark.parametrize(
    "body",
    [
        "nope",
        "[]",
        '{"price": {"amount": "1", "currency": "EUR"}, "transit_days": 1}',
        '{"carrier": " ", "price": {"amount": "1", "currency": "EUR"}, "transit_days": 1}',
        '{"carrier": "A", "price": {"amount": "0", "currency": "EUR"}, "transit_days": 1}',
        '{"carrier": "A", "price": {"amount": "1", "currency": "eur"}, "transit_days": 1}',
        '{"carrier": "A", "price": {"amount": "1", "currency": "EUR"}, "transit_days": 0}',
        '{"carrier": "A", "price": {"amount": "1", "currency": "EUR"}, "transit_days": true}',
        '{"carrier": "A", "price": {"amount": "1", "currency": "EUR"}, "transit_days": 1, "fuel_surcharge_pct": "-1"}',
    ],
)
def test_parse_quote_rejects_bad_answers(body):
    with pytest.raises(QuoteError):
        parse_quote(body)


def test_pick_best_prefers_lowest_total_then_speed_then_name():
    quotes = [quote("Zed", "100", 3), quote("Beta", "100", 2), quote("Alpha", "100", 2), quote("Pricey", "120", 1)]
    assert pick_best(quotes).carrier == "Alpha"
    assert pick_best([quote("A", "100", 2, "10"), quote("B", "105", 2)]).carrier == "B"


def test_pick_best_respects_transit_limit():
    quotes = [quote("Slow", "50", 6), quote("Fast", "90", 2)]
    assert pick_best(quotes, max_transit_days=3).carrier == "Fast"
    with pytest.raises(QuoteError):
        pick_best(quotes, max_transit_days=1)


def test_pick_best_rejects_empty_and_mixed_currencies():
    with pytest.raises(QuoteError):
        pick_best([])
    with pytest.raises(QuoteError):
        pick_best([quote("A", "1", 1), quote("B", "1", 1, currency="USD")])
