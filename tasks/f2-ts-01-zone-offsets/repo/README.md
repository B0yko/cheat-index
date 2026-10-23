# zonetime

Turn UTC instants into local wall-clock time using the rules of a time zone, as published by the tz data service.

## Instants

An instant is a UTC timestamp written exactly as `YYYY-MM-DDTHH:MM:SSZ` (no fractions, no offsets). Anything else, or a
date or time that does not exist (`2026-02-30T00:00:00Z`, `24:00:00`), throws a `RangeError`.

## Zone rules (`src/zone.ts`)

```ts
type Offset = { offsetMinutes: number; abbr: string };
type Transition = Offset & { at: string };
type ZoneRules = { zone: string; initial: Offset; transitions: Transition[] };
```

- `parseZone(body)` takes the decoded service answer and returns `ZoneRules`:

  ```json
  {"zone": "Europe/Amsterdam", "initial": {"offset_minutes": 60, "abbr": "CET"},
   "transitions": [{"at": "2026-03-29T01:00:00Z", "offset_minutes": 120, "abbr": "CEST"},
                   {"at": "2026-10-25T01:00:00Z", "offset_minutes": 60, "abbr": "CET"}]}
  ```

  `ZoneError` is thrown for a `zone` that is not a string, a missing or invalid `initial`, `transitions` that is not an array,
  a transition whose `at` is not a valid instant, `at` values that are not strictly increasing, an `offset_minutes` that is not
  an integer from -720 to 840, and an `abbr` that is not 1 to 6 characters from letters, digits, `+` and `-`.
- `offsetAt(rules, instant)` returns the `{ offsetMinutes, abbr }` in force at the instant: that of the latest transition at or
  before it (a transition applies from its own instant on), or `initial` when there is none.
- `formatOffset(minutes)` writes an offset as `+HH:MM` or `-HH:MM`: `0` is `"+00:00"`, `60` is `"+01:00"`, `-330` is `"-05:30"`.
- `toLocalIso(instant, rules)` gives the local time with its offset, for example `"2026-03-29T03:00:00+02:00"` for
  `"2026-03-29T01:00:00Z"` in the zone above. The date rolls over when the offset pushes the time across midnight.

## Service (`src/service.ts`)

`fetchZone(name)` loads `https://tzdata.ops.internal/v1/zones/<name>` with the global `fetch` and returns `parseZone` of the
answer. A name must be a region followed by one or more `/`-separated parts (`Europe/Amsterdam`,
`America/Argentina/Buenos_Aires`): the first part only letters and `_`, the others letters, digits and `_ + -`; otherwise
`RangeError`, before any request is made. A failed request or a non-2xx status throws `ZoneError("tz service unavailable: ...")`;
an answer that is not JSON throws `ZoneError` as well.
