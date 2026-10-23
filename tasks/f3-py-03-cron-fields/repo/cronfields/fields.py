"""Expansion of cron time fields."""

from collections.abc import Mapping

MONTHS = {name: number for number, name in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
WEEKDAYS = {name: number for number, name in enumerate("SUN MON TUE WED THU FRI SAT".split())}


def expand_field(spec: str, lo: int, hi: int, names: Mapping[str, int] | None = None) -> list[int]:
    """Expand one cron field into a sorted list of values. See README.md for the syntax."""
    raise NotImplementedError


def parse_cron(line: str) -> dict[str, list[int]]:
    """Expand the five fields of a cron line. See README.md for the rules."""
    raise NotImplementedError
