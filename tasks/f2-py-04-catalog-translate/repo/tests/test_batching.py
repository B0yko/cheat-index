from decimal import Decimal

import pytest

from msgtranslate import batch_texts, billable_characters, estimate_cost


def test_batches_keep_order_and_respect_max_items():
    assert batch_texts(["a", "b", "c", "d", "e"], max_items=2) == [["a", "b"], ["c", "d"], ["e"]]


def test_batches_respect_max_chars():
    texts = ["aaaa", "bbbb", "cc", "dddddd"]
    assert batch_texts(texts, max_chars=7) == [["aaaa"], ["bbbb", "cc"], ["dddddd"]]


def test_exact_fit_and_empty_input():
    assert batch_texts(["abcd", "efgh"], max_chars=8) == [["abcd", "efgh"]]
    assert batch_texts([]) == []


def test_oversized_text_is_rejected():
    with pytest.raises(ValueError):
        batch_texts(["x" * 11], max_chars=10)


def test_billable_characters_skip_placeholders():
    assert billable_characters(["Hi {name}!", "{a}{b}", ""]) == 4
    assert billable_characters(["Hello"]) == 5


def test_estimate_cost_rounds_up():
    assert estimate_cost(["a" * 3000], Decimal("20")) == Decimal("0.0600")
    assert estimate_cost(["a"], Decimal("20")) == Decimal("0.0001")
    assert estimate_cost([], Decimal("20")) == Decimal("0.0000")


def test_negative_price_is_rejected():
    with pytest.raises(ValueError):
        estimate_cost(["a"], Decimal("-1"))
