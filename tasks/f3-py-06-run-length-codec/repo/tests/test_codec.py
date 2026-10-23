import pytest

from runcodec import decode, encode


def test_runs():
    assert encode("QQQQQQQrstUUU") == "7Qrst3U"


def test_escapes():
    assert encode(r"ab11\9999") == r"ab\1\1\\4\9"
    assert decode(r"12k\5mm4\\") == "k" * 12 + "5mm" + "\\" * 4


def test_count_without_character():
    with pytest.raises(ValueError):
        decode("17")
