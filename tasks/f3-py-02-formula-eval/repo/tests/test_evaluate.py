import pytest

from rulecalc import EvalError, evaluate


def test_precedence_and_variables():
    assert evaluate("1250 * (1 - discount) + 17", {"discount": 0.25}) == 954.5


def test_functions_and_modulo():
    assert evaluate("max(unit * qty, 4999) - min(7, 31 % 9)", {"unit": 125, "qty": 41}) == 5121


def test_malformed_formula():
    with pytest.raises(EvalError):
        evaluate("3 + * 11")
