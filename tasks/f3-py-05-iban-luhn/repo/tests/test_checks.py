from bankcheck import iban_check_digits, iban_valid, luhn_valid


def test_luhn():
    assert luhn_valid("5301 7743 9026 1183")
    assert not luhn_valid("5301 7743 9026 1184")


def test_iban():
    assert iban_valid("NL43 TXNB 0847 2619 35")
    assert not iban_valid("AT36 2011 1284 7395 0265")


def test_check_digits():
    assert iban_check_digits("DE", "372100550318746029") == "39"
