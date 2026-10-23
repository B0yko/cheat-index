# freight

Carrier rate quotes for pallet shipments, read from the freight rate service.

## Rate service

`GET https://rates.freight.internal/v3/quote?from=NLRTM&to=DEHAM&kg=420` answers with JSON:

```json
{"carrier": "Harborline", "price": {"amount": "137.50", "currency": "EUR"}, "transit_days": 2, "fuel_surcharge_pct": "6.5"}
```

`from` and `to` are five-character UN/LOCODE port codes. The service answers `404` when no carrier serves the route.

## Quotes (`freight/quote.py`)

`Quote(carrier, base_amount, currency, transit_days, fuel_surcharge_pct=Decimal(0))` has a `total` property:
`base_amount * (1 + fuel_surcharge_pct / 100)`, rounded half up to cents.

- `parse_quote(body: str) -> Quote` reads a service answer. `QuoteError` for text that is not a JSON object, a missing
  or blank `carrier` (it must be a non-blank string), a `price` without a positive, finite decimal `amount` or without a
  three-letter uppercase `currency`, a
  `transit_days` that is not an integer of at least 1 (booleans do not count), and a `fuel_surcharge_pct` (optional,
  default 0) that is not a non-negative decimal. Amounts may be JSON strings or numbers.
- `pick_best(quotes, *, max_transit_days=None) -> Quote` returns the quote with the lowest `total`; ties go to fewer
  transit days, then to the carrier name in alphabetical order. Quotes slower than `max_transit_days` are not
  considered. `QuoteError` when nothing is left (or `quotes` is empty), and when the quotes use different currencies
  (checked on all given quotes, before the limit is applied).

## Client (`freight/client.py`)

`FreightClient(base_url="https://rates.freight.internal/v3", transport=None)`

`transport` is a callable `transport(request, timeout) -> bytes` that performs the HTTP request and returns the response
body. The default transport calls `urllib.request.urlopen`. Pass another one to run without the service. A trailing `/` on
`base_url` is ignored.

- `quote(origin, destination, weight_kg, *, timeout=10.0) -> Quote` requests
  `{base_url}/quote?from=<origin>&to=<destination>&kg=<weight_kg>` and parses the body.
- `origin` and `destination` must be two uppercase letters followed by three uppercase letters or digits; `weight_kg` must
  be an `int` from 1 to 20000 (booleans do not count). Otherwise `ValueError`, before anything is requested.
- HTTP status 404 raises `NoRouteError`. Other HTTP errors and network failures raise
  `QuoteError("rate service unavailable: ...")`. A body that is not valid UTF-8 raises `QuoteError` too. `NoRouteError` is a
  subclass of `QuoteError`.
