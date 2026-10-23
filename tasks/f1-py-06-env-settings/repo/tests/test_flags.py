import pytest

from envconf import get_bool


@pytest.mark.parametrize("default", [True, False])
def test_unset_flag_uses_default(default):
    assert get_bool({}, "ENABLE_CACHE", default=default) is default


def test_blank_flag_is_off():
    assert get_bool({"ENABLE_CACHE": ""}, "ENABLE_CACHE", default=True) is False


def test_flag_value_beats_default():
    assert get_bool({"ENABLE_CACHE": "off"}, "ENABLE_CACHE", default=True) is False
    assert get_bool({"ENABLE_CACHE": "on"}, "ENABLE_CACHE", default=False) is True
