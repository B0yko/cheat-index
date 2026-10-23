import pytest

from msgtranslate import PlaceholderError, protect, restore


def test_protect_numbers_placeholders_in_order():
    assert protect("Hi {name}, {n} new") == ('Hi <ph n="0"/>, <ph n="1"/> new', ["{name}", "{n}"])


def test_repeated_placeholders_get_their_own_number():
    masked, tokens = protect("{a} and {a}")
    assert masked == '<ph n="0"/> and <ph n="1"/>'
    assert tokens == ["{a}", "{a}"]


def test_text_without_placeholders_is_unchanged():
    assert protect("Plain text, {not valid} {1x} {}") == ("Plain text, {not valid} {1x} {}", [])


def test_restore_round_trip():
    masked, tokens = protect("Dear {user_name}, you owe {amount}.")
    assert restore(masked, tokens) == "Dear {user_name}, you owe {amount}."


def test_restore_accepts_reordered_tags_and_spacing():
    assert restore('<ph n="1"/> kommt vor <ph n="0" />', ["{a}", "{b}"]) == "{b} kommt vor {a}"


@pytest.mark.parametrize(
    "translated",
    ['only <ph n="0"/>', '<ph n="0"/> <ph n="0"/> <ph n="1"/>', 'x <ph n="0"/> <ph n="1"/> <ph n="2"/>', "no tags"],
)
def test_restore_rejects_damaged_texts(translated):
    with pytest.raises(PlaceholderError):
        restore(translated, ["{a}", "{b}"])
