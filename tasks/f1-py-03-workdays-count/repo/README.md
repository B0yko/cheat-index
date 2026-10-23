# workdays

Working-day arithmetic for the support desk's SLA clock. Saturday and Sunday are never working days, and callers
can pass a collection of holiday dates that are skipped as well.

## `is_business_day(day, holidays=())`

`True` when `day` is Monday to Friday and not one of `holidays`.

## `business_days_between(start, end, holidays=())`

How many business days there are from `start` up to `end`. The range is half-open: `start` is counted (when it is a
business day) and `end` is **not**. For example, from Monday 2025-03-03 to Monday 2025-03-10 there are 5 business days.

- `start == end` gives `0`.
- `end` before `start` raises `ValueError`.
- A holiday only reduces the count when it is a weekday inside the range; holidays on weekends or outside the range
  are ignored, and a date listed twice counts once.

## `add_business_days(start, count, holidays=())`

The date that is `count` business days after `start`. Counting begins the day after `start`, and only business days
are counted, so Friday 2025-03-07 plus 1 is Monday 2025-03-10. `count == 0` returns `start` unchanged, even when it
falls on a weekend. A negative `count` raises `ValueError`.

## `next_business_day(day, holidays=())`

The first business day on or after `day`: a business day is returned as is, a Saturday gives the following Monday.
