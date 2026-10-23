import pytest

from smsgate import detect_encoding, plan_segments


def test_short_gsm_text_is_one_part():
    plan = plan_segments("Your code is 123456")
    assert (plan.encoding, plan.units, plan.parts) == ("gsm7", 19, ["Your code is 123456"])


def test_gsm_limit_and_split():
    assert len(plan_segments("a" * 160).parts) == 1
    plan = plan_segments("a" * 161)
    assert [len(p) for p in plan.parts] == [153, 8]


def test_extended_characters_cost_two_units():
    plan = plan_segments("{}" * 40)
    assert (plan.encoding, plan.units, len(plan.parts)) == ("gsm7", 160, 1)
    assert plan_segments("price: 5\u20ac").units == 10


def test_extended_character_is_not_split_across_parts():
    plan = plan_segments("a" * 152 + "{" + "b" * 10)
    assert plan.units == 164
    assert plan.parts == ["a" * 152, "{" + "b" * 10]


def test_other_characters_force_ucs2():
    assert detect_encoding("caf\u00e9") == "ucs2"
    plan = plan_segments("\u041f\u0440\u0438\u0432\u0456\u0442")
    assert (plan.encoding, plan.units, len(plan.parts)) == ("ucs2", 6, 1)


def test_ucs2_limit_and_split():
    assert len(plan_segments("\u044f" * 70).parts) == 1
    assert [len(p) for p in plan_segments("\u044f" * 71).parts] == [67, 4]


def test_emoji_counts_two_units_and_is_not_split():
    plan = plan_segments("\u044f" * 66 + "\U0001F600" + "\u044f" * 5)
    assert plan.units == 73
    assert plan.parts == ["\u044f" * 66, "\U0001F600" + "\u044f" * 5]


def test_parts_join_back_to_the_text():
    text = "Order {1042} shipped | track at example.org/t/9 " * 6
    assert "".join(plan_segments(text).parts) == text


def test_empty_text_is_rejected():
    with pytest.raises(ValueError):
        plan_segments("")
