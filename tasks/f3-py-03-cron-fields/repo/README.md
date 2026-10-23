# cronfields

Reads the five time fields of a cron line and says which values each one selects.

## `expand_field(spec, lo, hi, names=None) -> list[int]`

Expands one cron field into the sorted list of values it selects, all within `lo..hi` (inclusive).

A field is one or more items separated by commas. An item is one of:

| item    | selects                                                        |
|---------|----------------------------------------------------------------|
| `*`     | every value from `lo` to `hi`                                  |
| `N`     | the single value `N`                                           |
| `A-B`   | every value from `A` to `B`                                    |
| `*/S`   | every `S`-th value, starting at `lo`                           |
| `A-B/S` | every `S`-th value from `A` up to `B`, starting at `A`         |

- Numbers are plain decimal digits (`07` is 7). `names` may map upper-case names to values (`{"JAN": 1, ...}`); a
  name is then accepted wherever a number is, and matched without regard to case.
- Every number must be within `lo..hi`, `A` must not be greater than `B` (no wrapping around) and `S` must be at
  least 1.
- Items may overlap. Every value appears once in the result.
- Anything else raises `ValueError`: empty items (`""`, `"1,,2"`), a step without `*` or a range (`5/2`), signs,
  spaces, decimals, unknown names.

`expand_field("*/20", 0, 59)` is `[0, 20, 40]`, and `expand_field("2,10-12,11", 0, 23)` is `[2, 10, 11, 12]`.

## `parse_cron(line) -> dict[str, list[int]]`

Splits a cron line on runs of whitespace into exactly five fields and expands each with its own range:

| key       | field | range | names                      |
|-----------|-------|-------|----------------------------|
| `minute`  | 1st   | 0-59  |                            |
| `hour`    | 2nd   | 0-23  |                            |
| `day`     | 3rd   | 1-31  |                            |
| `month`   | 4th   | 1-12  | `JAN` to `DEC`             |
| `weekday` | 5th   | 0-7   | `SUN` (0) to `SAT` (6)     |

In the weekday field both `0` and `7` mean Sunday. The result uses `0` for it and lists it in sorted position, so
`5-7` gives `[0, 5, 6]`. A line that does not have exactly five fields raises `ValueError`, and so does an invalid
field.
