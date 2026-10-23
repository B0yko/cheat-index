from rowcheck import Column, check_value


def test_blank_required_value():
    assert check_value(Column("name"), "   ") == "is required"


def test_blank_optional_value_is_fine():
    assert check_value(Column("note", required=False), "") is None


def test_int_must_be_a_whole_number():
    age = Column("age", "int")
    assert check_value(age, " 42 ") is None
    assert check_value(age, "4.5") == "must be a whole number"
    assert check_value(age, "forty") == "must be a whole number"


def test_int_range():
    qty = Column("qty", "int", min_value=1, max_value=99)
    assert check_value(qty, "0") == "must be at least 1"
    assert check_value(qty, "100") == "must be at most 99"
    assert check_value(qty, "99") is None


def test_date_must_be_a_real_calendar_date():
    due = Column("due", "date")
    assert check_value(due, "2024-02-29") is None
    assert check_value(due, "2023-02-29") == "must be a date (YYYY-MM-DD)"
    assert check_value(due, "02/03/2024") == "must be a date (YYYY-MM-DD)"


def test_choice_lists_the_allowed_values():
    size = Column("size", "choice", choices=("S", "M", "L"))
    assert check_value(size, "M") is None
    assert check_value(size, "m") == "must be one of: S, M, L"


def test_text_length_limit():
    code = Column("code", max_length=5)
    assert check_value(code, " ABCDE ") is None
    assert check_value(code, "ABCDEF") == "must be at most 5 characters"
