import pytest

from slugs import slugify


def test_words_are_lowercased_and_joined():
    assert slugify("Hello World") == "hello-world"


def test_accents_are_removed():
    assert slugify("Crème Brûlée") == "creme-brulee"


def test_runs_of_punctuation_become_one_hyphen():
    assert slugify("  Rock & Roll -- Forever!!  ") == "rock-roll-forever"


def test_apostrophes_are_dropped():
    assert slugify("Don't Stop Believin'") == "dont-stop-believin"


def test_letters_without_an_accent_form_are_spelled_out():
    assert slugify("Straße") == "strasse"


def test_nothing_left_gives_untitled():
    assert slugify("!!!") == "untitled"


def test_long_slugs_are_cut_at_a_word_boundary():
    assert slugify("the quick brown fox jumps", max_length=12) == "the-quick"
    assert slugify("the quick brown fox jumps", max_length=15) == "the-quick-brown"


def test_a_long_first_word_is_cut_in_the_middle():
    assert slugify("supercalifragilistic", max_length=10) == "supercalif"


def test_max_length_must_be_positive():
    with pytest.raises(ValueError):
        slugify("anything", max_length=0)
