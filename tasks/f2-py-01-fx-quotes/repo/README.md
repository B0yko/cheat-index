# fxquote

Currency conversion for invoices, based on the daily reference rates that the treasury team publishes.

## Rate service

`GET https://fx.treasury.internal/v1/rates?base=EUR` answers with JSON:

```json
{"base": "EUR", "as_of": "2026-03-02T09:30:00Z", "rates": {"USD": "1.0842", "GBP": "0.8561", "JPY": "162.30"}}
```

A rate says how many units of that currency one unit of `base` buys. Rates are decimal strings.

## API

### `parse_rates(text: str) -> RateTable`

Parses a response body. `RateTable` has `base` (str), `as_of` (str, exactly as published) and `rates`
(`dict[str, Decimal]`).

- The base currency is always in `rates` with rate `1`. A rate listed for the base itself in the payload is ignored.
- `RateError` is raised for text that is not valid JSON, a payload without `base`, a string `as_of` or a `rates` object, a
  currency code that is not three uppercase letters, and a rate that is not a positive, finite decimal.

### `fetch_rates(base: str = "EUR", *, timeout: float = 5.0) -> RateTable`

Requests the URL above (query parameter `base`) with `urllib.request.urlopen` and parses the body.

- A `base` that is not three uppercase letters raises `RateError` before any request is made.
- Network failures, timeouts and non-200 answers raise `RateError("rate service unavailable: ...")`.

### `convert(amount: Decimal, source: str, target: str, table: RateTable) -> Decimal`

Converts through the table's base currency: `amount * rate(target) / rate(source)`.

- The result is rounded to the minor unit of `target`: 2 decimals by default, 0 for `JPY` and `KRW`, 3 for `KWD`
  and `BHD`. Ties round away from zero (`0.005` becomes `0.01`, `-0.005` becomes `-0.01`).
- Negative amounts are allowed (refunds). Converting a currency to itself just rounds.
- A currency that is not in the table raises `RateError`.

### `format_amount(amount: Decimal, code: str) -> str`

Formats an amount for an invoice line: thousands separators, the minor unit of `code`, then the code, for example
`"1,234.50 USD"` or `"162,300 JPY"`. Rounding follows `convert`.
