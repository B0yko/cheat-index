# durations

Small helpers for showing elapsed time to people.

## `format_duration(seconds: int) -> str`

Formats a whole number of seconds as hours, minutes and seconds, for example `3725` becomes `"1h 2m 5s"`.

- Units are `h`, `m` and `s`, largest first, separated by single spaces.
- A unit whose value is zero is left out: `3600` is `"1h"`, `61` is `"1m 1s"`.
- Zero seconds is `"0s"`.
- Hours are not rolled into days: `90000` is `"25h"`.
- A negative duration is a programming error: `format_duration` raises `ValueError`.
- Anything that is not an `int` (including `bool`) raises `TypeError`.
