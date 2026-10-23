import pytest

from cronfields import expand_field, parse_cron


def test_lists_ranges_and_steps():
    assert expand_field("5,17-23/3,40", 0, 59) == [5, 17, 20, 23, 40]


def test_whole_line():
    assert parse_cron("*/25 6-9 1,15 MAR-MAY mon-fri") == {
        "minute": [0, 25, 50],
        "hour": [6, 7, 8, 9],
        "day": [1, 15],
        "month": [3, 4, 5],
        "weekday": [1, 2, 3, 4, 5],
    }


def test_out_of_range_value():
    with pytest.raises(ValueError):
        expand_field("61", 0, 59)
