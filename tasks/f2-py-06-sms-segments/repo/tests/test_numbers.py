import pytest

from smsgate import normalize_number


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+44 20 7946 0958", "+442079460958"),
        ("020 7946 0958", "+442079460958"),
        ("0044 20 7946 0958", "+442079460958"),
        ("(020) 7946-0958", "+442079460958"),
        ("+1 (415) 555-0132", "+14155550132"),
    ],
)
def test_normalised_numbers(raw, expected):
    assert normalize_number(raw) == expected


def test_default_country_code():
    assert normalize_number("067 123 45 67", default_cc="380") == "+380671234567"


@pytest.mark.parametrize("raw", ["", "12345", "+12", "+0123456789", "+44 abc 123 4567", "7946 0958 20"])
def test_invalid_numbers(raw):
    with pytest.raises(ValueError):
        normalize_number(raw)
