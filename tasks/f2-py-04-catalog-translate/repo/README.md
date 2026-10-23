# msgtranslate

Translate the strings of a message catalog (`{"greeting": "Hello, {name}!"}`) with the LingoForge translation API.
The API is a paid service that bills per character, so the helpers here keep requests small and predictable.

## Placeholders (`msgtranslate/placeholders.py`)

Translation engines mangle `{name}`, so placeholders are swapped for XML tags before sending.

- `protect(text) -> (masked, tokens)` replaces every placeholder (`{` letter or underscore, then letters, digits or
  underscores, `}`) with `<ph n="K"/>`, where `K` counts from 0 in order of appearance (a repeated placeholder gets its
  own number). `tokens` is the list of original placeholders, so
  `protect("Hi {name}, {n} new")` is `('Hi <ph n="0"/>, <ph n="1"/> new', ["{name}", "{n}"])`.
- `restore(text, tokens) -> str` puts the originals back. A tag may have whitespace before `/>`. Every index of
  `tokens` must occur exactly once in `text` and no tag may use an index outside `tokens`, otherwise
  `PlaceholderError`.

## Batching and cost (`msgtranslate/batching.py`)

- `batch_texts(texts, *, max_items=50, max_chars=5000) -> list[list[str]]` splits texts in order into batches of at
  most `max_items` texts and at most `max_chars` characters in total (greedy: start a new batch when the next text would
  not fit). A single text longer than `max_chars` raises `ValueError`.
- `billable_characters(texts) -> int` is the sum of the lengths of the texts with their `{placeholders}` removed
  (the API does not bill tags).
- `estimate_cost(texts, price_per_million) -> Decimal` is `billable_characters / 1,000,000 * price_per_million`,
  rounded up (towards +infinity) to 4 decimals. A negative price raises `ValueError`.

## Client (`msgtranslate/client.py`)

`TranslateClient(api_key, base_url="https://api.lingoforge.example/v1")`

- A blank key raises `MissingKeyError`; surrounding whitespace is stripped from the key. `TranslateClient.from_env(env=None)`
  reads `LINGOFORGE_API_KEY` (`env` defaults to `os.environ`) and raises `MissingKeyError` when it is missing or blank.
- `build_request(masked_texts, target, source=None)` returns `POST {base_url}/translate` as a
  `urllib.request.Request` with the header `Authorization: ApiKey <key>`, `Content-Type: application/json` and the JSON
  body `{"q": masked_texts, "target": target, "tag_handling": "xml"}` (plus `"source"` when given). Language codes
  look like `de` or `pt-BR` (two lowercase letters, optionally a dash and two uppercase letters); anything else is a
  `ValueError`, and so is an empty list of texts.
- `parse_response(body, expected) -> list[str]` reads `{"translations": [{"text": "..."}, ...]}` and returns the texts.
  Invalid JSON, a different shape or a count other than `expected` raises `TranslateError`.
- `translate(texts, target, source=None, *, timeout=30.0) -> list[str]` protects the placeholders, sends the texts in
  batches with `urllib.request.urlopen`, and returns the translations in order with placeholders restored. Bad language
  codes raise the same `ValueError` as `build_request`, before anything is sent. An empty list returns `[]` without any
  request. An HTTP error answer raises `TranslateError("translation service refused the
  request: ...")` with `invalid API key` for 401 and 403, `quota exhausted` for 402, `rate limited` for 429 and `HTTP
  <code>` otherwise; other network failures raise `TranslateError("translation service request failed: ...")`.
