# alertwatch

Evaluate alert rules over metric series from the internal metrics service.

## Metrics service

`GET https://metrics.ops.internal/v1/series?metric=queue_depth&window=900` answers with JSON:

```json
{"metric": "queue_depth", "samples": [{"t": 1700000000, "v": 12.5}, {"t": 1700000060, "v": 14}]}
```

`t` is a Unix timestamp in seconds, `v` the value. A metric name is lowercase letters, digits and `_`, starting with a letter,
at most 63 characters.

## Series (`src/series.ts`)

`parseSeries(body)` takes the decoded JSON and returns `{ t, v }[]`. `MetricsError` is thrown for a body without a `samples`
array, a `t` that is not a non-negative integer, `t` values that are not strictly increasing, and a `v` that is not a finite
number.

## Client (`src/client.ts`)

`new MetricsClient({ baseUrl = "https://metrics.ops.internal/v1", fetchImpl = fetch } = {})`. `fetchImpl` is called as
`fetchImpl(url)` with the full URL as a string and must resolve to a `Response`; pass a stub to run without the service.

`await client.getSeries(metric, windowSeconds)` requests `<baseUrl>/series?metric=<metric>&window=<windowSeconds>` (a trailing
`/` on `baseUrl` is dropped) and returns `parseSeries` of the answer.

- A metric name that does not follow the rule above, or a window that is not an integer from 60 to 86400, throws `RangeError`
  before any request is made.
- A rejected `fetchImpl` call throws `MetricsError("metrics service unavailable: <message>")`. A non-2xx status throws
  `MetricsError("metrics service answered HTTP <status>")`. An answer that is not JSON throws `MetricsError`.

## Rules (`src/rules.ts`)

A rule is `{ threshold, above, forSeconds }`: `threshold` a finite number, `above` a boolean, `forSeconds` an integer of at
least 0; otherwise `RangeError`. A sample breaches the rule when `v > threshold` (`above: true`) or `v < threshold`
(`above: false`); equal to the threshold never breaches.

- `evaluateRule(samples, rule)` looks at the run of consecutive breaching samples that ends at the last sample and returns
  `{ state, since, value }`. With no samples or when the last sample does not breach: `{ state: "ok", since: null, value }`
  where `value` is the last sample's value (`null` without samples). Otherwise `since` is the `t` of the first sample of the
  run, `value` the last value, and `state` is `"firing"` when the last `t` minus `since` is at least `forSeconds`, else
  `"pending"`.
- `findIncidents(samples, rule)` returns `{ from, to, peak }[]` for every maximal run of consecutive breaching samples that
  lasts at least `forSeconds` (`to - from`, using the `t` of the first and last sample of the run), oldest first. `peak` is the
  largest `v` of the run for `above: true` and the smallest for `above: false`. A run of a single sample lasts 0 seconds.
