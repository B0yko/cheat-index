import pytest

from durations import format_duration


def test_hours_minutes_seconds():
    assert format_duration(3725) == "1h 2m 5s"


def test_zero_units_are_omitted():
    assert format_duration(3600) == "1h"
    assert format_duration(61) == "1m 1s"


def test_zero():
    assert format_duration(0) == "0s"


def test_negative_seconds():
    assert format_duration(-5) == "-5s"


def test_rejects_non_int():
    with pytest.raises(TypeError):
        format_duration(1.5)
