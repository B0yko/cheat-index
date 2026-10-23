import pytest

from envconf import SettingError, get_bool, get_int, get_list, get_str


def test_str_is_stripped():
    assert get_str({"NAME": "  api  "}, "NAME") == "api"


def test_missing_str_uses_default():
    assert get_str({}, "NAME", default="worker") == "worker"
    assert get_str({}, "NAME") is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1", True), ("TRUE", True), ("yes", True), ("On", True), ("0", False), ("False", False), ("no", False), ("OFF", False)],
)
def test_bool_words(raw, expected):
    assert get_bool({"FLAG": raw}, "FLAG") is expected


def test_bool_rejects_other_words():
    with pytest.raises(SettingError, match="FLAG"):
        get_bool({"FLAG": "maybe"}, "FLAG")


def test_int_accepts_signs_and_padding():
    assert get_int({"PORT": " 8080 "}, "PORT") == 8080
    assert get_int({"OFFSET": "-15"}, "OFFSET") == -15
    assert get_int({"OFFSET": "+7"}, "OFFSET") == 7


def test_int_rejects_text_and_out_of_range():
    with pytest.raises(SettingError):
        get_int({"PORT": "80.5"}, "PORT")
    with pytest.raises(SettingError):
        get_int({"PORT": "70000"}, "PORT", minimum=1, maximum=65535)


def test_list_is_split_and_cleaned():
    assert get_list({"HOSTS": "a, b,,c,"}, "HOSTS") == ["a", "b", "c"]


def test_blank_values_count_as_unset():
    assert get_bool({"DEBUG": ""}, "DEBUG", default=True) is True
    assert get_int({"PORT": "   "}, "PORT", default=8080) == 8080
    assert get_str({"NAME": " "}, "NAME", default="worker") == "worker"
