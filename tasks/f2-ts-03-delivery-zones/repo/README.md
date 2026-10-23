# shipzones

Work out the delivery zone of a street address. Addresses are turned into coordinates by the MapSmith geocoding API, a paid
service that is billed per request.

## Geometry (`src/geo.ts`)

- `haversineKm(a, b)` is the great-circle distance in kilometres between two `{ lat, lng }` points, using a mean Earth
  radius of 6371.0088 km. Coordinates must be finite numbers with `lat` in -90..90 and `lng` in -180..180, otherwise
  `RangeError`.
- `zoneFor(distanceKm)` gives the delivery zone: `"A"` up to 25 km, `"B"` up to 100 km, `"C"` up to 400 km, `"D"` up to 1000 km
  and `"E"` beyond. The upper bounds are inclusive. A negative or non-finite distance throws `RangeError`.

## Geocoding (`src/geocode.ts`)

- `normalizeAddress(raw)` splits on commas, trims every part, collapses runs of whitespace to one space, drops empty parts and
  joins the rest with `", "`. An address with nothing left throws `RangeError`.
- `buildGeocodeRequest(address, apiKey, baseUrl = "https://api.mapsmith.example/v2")` returns `{ url, headers }`. The URL is
  `<baseUrl>/geocode?q=<normalised address, encoded with encodeURIComponent>&limit=3` (a trailing `/` on `baseUrl` is dropped)
  and the headers are `Authorization: Bearer <apiKey>` and `Accept: application/json`. A blank key throws `MissingApiKeyError`;
  keys are trimmed of surrounding whitespace everywhere (request headers, constructor, `fromEnv`).
- `parseGeocodeResponse(body)` takes the decoded answer `{ "results": [{ "lat": 51.92, "lng": 4.47, "confidence": 0.93 }] }` and
  returns the best point as `{ lat, lng, confidence }`. Entries whose coordinates are out of range or not numbers, or whose
  confidence is not a number from 0 to 1, are ignored. Only confidence 0.5 or higher counts; the highest wins and the first
  one wins a tie. `null` when nothing qualifies. A body without a `results` array throws `GeocodeError`.
- `new Geocoder(apiKey, baseUrl?)` throws `MissingApiKeyError` for a blank key. `Geocoder.fromEnv(env = process.env)` reads the key
  from `MAPSMITH_API_KEY` (and an optional base URL from `MAPSMITH_API_URL`) and throws `MissingApiKeyError` when the key is
  missing or blank.
- `await geocoder.geocode(address)` requests the URL from `buildGeocodeRequest` with the global `fetch` and returns
  `parseGeocodeResponse` of the answer. A failed request throws `GeocodeError("geocoding service unavailable: ...")`; status 401
  or 403 throws `GeocodeError("API key rejected")`, 402 `GeocodeError("quota exhausted")`, 429 `GeocodeError("rate limited")` and
  any other non-2xx status `GeocodeError("geocoding service answered HTTP <status>")`. An answer that is not JSON throws
  `GeocodeError`.
