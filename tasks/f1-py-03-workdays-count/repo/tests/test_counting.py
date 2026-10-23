from datetime import date

import pytest

from workdays import add_business_days, business_days_between, is_business_day, next_business_day

MON = date(2025, 3, 3)
WED = date(2025, 3, 5)
FRI = date(2025, 3, 7)
SAT = date(2025, 3, 8)
NEXT_MON = date(2025, 3, 10)


def test_weekends_are_not_business_days():
    assert is_business_day(MON)
    assert not is_business_day(SAT)
    assert not is_business_day(date(2025, 3, 9))


def test_holiday_is_not_a_business_day():
    assert not is_business_day(WED, holidays={WED})


def test_work_week_count():
    # Monday to Friday of the same week
    assert business_days_between(MON, FRI) == 5


def test_weekend_is_skipped():
    assert business_days_between(MON, SAT) == 5


def test_holiday_reduces_the_count():
    assert business_days_between(MON, SAT, holidays=[WED]) == 4


def test_end_before_start_is_rejected():
    with pytest.raises(ValueError):
        business_days_between(FRI, MON)


def test_add_skips_the_weekend():
    assert add_business_days(FRI, 1) == NEXT_MON


def test_add_a_full_week():
    assert add_business_days(WED, 5) == date(2025, 3, 12)


def test_add_skips_holidays():
    assert add_business_days(MON, 3, holidays={date(2025, 3, 4)}) == FRI


def test_next_business_day():
    assert next_business_day(SAT) == NEXT_MON
    assert next_business_day(WED) == WED
