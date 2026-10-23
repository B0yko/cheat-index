"""Checking whole CSV files."""

from rowcheck.schema import Column, Problem


def check_csv(text: str, columns: list[Column]) -> list[Problem]:
    """Check every row of `text` against `columns`. See README.md for the rules."""
    raise NotImplementedError
