"""Counting and shifting working days. See README.md for the rules."""

from collections.abc import Collection
from datetime import date


def is_business_day(day: date, holidays: Collection[date] = ()) -> bool:
    """True for Monday to Friday unless `day` is a holiday."""
    return day.weekday() < 5 and day not in holidays


def business_days_between(start: date, end: date, holidays: Collection[date] = ()) -> int:
    """Number of business days from `start` up to `end`."""
    raise NotImplementedError


def add_business_days(start: date, count: int, holidays: Collection[date] = ()) -> date:
    """The date `count` business days after `start`."""
    raise NotImplementedError


def next_business_day(day: date, holidays: Collection[date] = ()) -> date:
    """The first business day on or after `day`."""
    raise NotImplementedError
