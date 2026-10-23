"""Checks for card and bank account numbers."""

IBAN_LENGTHS = {
    "AT": 20,
    "BE": 16,
    "CH": 21,
    "DE": 22,
    "DK": 18,
    "ES": 24,
    "FR": 27,
    "GB": 22,
    "IE": 22,
    "IT": 27,
    "LU": 20,
    "NL": 18,
    "NO": 15,
    "PL": 28,
    "PT": 25,
    "SE": 24,
}


def luhn_valid(number: str) -> bool:
    """Luhn check of a digit string. See README.md."""
    raise NotImplementedError


def iban_valid(iban: str) -> bool:
    """Structure, length and check digits of an IBAN. See README.md."""
    raise NotImplementedError


def iban_check_digits(country: str, account: str) -> str:
    """The two IBAN check digits for an account part. See README.md."""
    raise NotImplementedError
