# rowcheck

Checks the rows of an uploaded CSV file against a list of column definitions before the data is imported.

## Columns

```python
Column(name, kind="text", required=True, choices=(), min_value=None, max_value=None, max_length=None)
```

`kind` is `"text"`, `"int"`, `"date"` or `"choice"`.

## `check_value(column, raw) -> str | None`

Returns `None` when `raw` is acceptable, otherwise a short message. Whitespace around the value is ignored.

1. A blank value is `"is required"` for a required column and fine for an optional one. No other check runs on a
   blank value.
2. `int`: an optional leading `-` and digits only, otherwise `"must be a whole number"`. Then `min_value` and
   `max_value` when set: `"must be at least 3"`, `"must be at most 99"`.
3. `date`: a real calendar date written `YYYY-MM-DD`, otherwise `"must be a date (YYYY-MM-DD)"`.
4. `choice`: the value must be one of `choices`, compared exactly (case matters), otherwise
   `"must be one of: S, M, L"` (the choices in their given order).
5. `text`: when `max_length` is set, a longer value gives `"must be at most 12 characters"`.
6. Any other `kind` raises `ValueError`.

## `check_csv(text, columns) -> list[Problem]`

`Problem(row, column, message)`. `text` is the whole file; the first record is the header and records are numbered
from 1, so the header is row 1 and the first data record is row 2.

- Header names are compared after trimming. The order of the columns in the file does not matter and columns that are
  not declared are ignored.
- A required column that is missing from the header gives one `Problem(1, name, "column is missing")` and its values
  are not checked. A missing optional column is fine.
- A file with no records, or only blank ones, gives `[Problem(1, "*", "file is empty")]`.
- Blank records (no fields, or only blank fields) are skipped, but they still count when numbering rows.
- A record with a different number of fields than the header gives one `Problem(row, "*", "expected 3 fields, found 2")`
  and its values are not checked.
- Otherwise each declared column that is present is checked with `check_value`. Problems are listed by row, and within
  a row in the order the columns were declared.
