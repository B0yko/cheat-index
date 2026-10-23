"""Evaluation of small arithmetic formulas."""

from collections.abc import Mapping


class EvalError(ValueError):
    """The formula is malformed or cannot be evaluated."""


def evaluate(formula: str, variables: Mapping[str, int | float] | None = None) -> int | float:
    """Evaluate `formula`. See README.md for the language."""
    raise NotImplementedError
