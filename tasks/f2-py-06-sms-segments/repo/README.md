# smsgate

Prepare text messages for the SMS gateway: choose the encoding, split long texts into segments and build the request.

## Segments (`smsgate/segments.py`)

`plan_segments(text) -> SegmentPlan(encoding, units, parts)`

- The gateway's 7-bit alphabet (`gsm7`) is the letters `a-z` and `A-Z`, the digits, space, newline and
  ``. , : ; ! ? @ # % & * ( ) - + = / _ ' " < > $ £``. The characters ``{ } [ ] \ ~ ^ | €`` are in the alphabet too but cost
  two units each. Text made only of these characters is `gsm7`; any other character (`é`, `ж`, an emoji) makes the
  whole text `ucs2`.
- `units` is the cost of the whole text: for `gsm7` the sum of the character costs above, for `ucs2` the number of
  UTF-16 code units (a character outside the Basic Multilingual Plane, like an emoji, counts 2).
- A text of at most 160 units (`gsm7`) or 70 units (`ucs2`) is a single part. A longer text is split into parts of at
  most 153 (`gsm7`) or 67 (`ucs2`) units, filled greedily from the left. A character is never split: a two-unit
  character that does not fit moves to the next part.
- `parts` are strings; joined together they give the original text. Empty text raises `ValueError`.

## Phone numbers (`smsgate/numbers.py`)

`normalize_number(raw, default_cc="44") -> str` returns the number in E.164 form.

- Spaces, dots, hyphens and parentheses are removed first.
- A leading `00` is replaced by `+`. A single leading `0` is a national number: it is replaced by `+` and the
  `default_cc`. A leading `+` is kept.
- The result must be `+`, a digit from 1 to 9, and 7 to 14 more digits; otherwise `ValueError` (this includes numbers that
  have no `+`, `00` or `0` prefix, and numbers with letters).

## Gateway client (`smsgate/client.py`)

`SmsClient(token, base_url="https://sms.gateway.internal/v1")`

- A blank token raises `MissingTokenError`; surrounding whitespace is stripped from the token. `SmsClient.from_env(env=None)` reads the token from `SMS_GATEWAY_TOKEN`
  (`env` defaults to `os.environ`) and raises `MissingTokenError` when it is missing or blank.
- `build_request(to, text, *, default_cc="44")` returns a `urllib.request.Request`: `POST {base_url}/messages`, header
  `Authorization: Token <token>`, `Content-Type: application/json` and a JSON body
  `{"to": <normalised number>, "encoding": ..., "parts": [...]}` from `normalize_number` and `plan_segments`.
- `send(to, text, *, default_cc="44", timeout=10.0)` builds that request (so it raises the same `ValueError`s as
  `build_request`, before anything is sent), sends it with `urllib.request.urlopen` and returns the decoded JSON answer.
  Network failures and answers that are not JSON raise `GatewayError`.
