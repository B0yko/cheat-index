# dnsync

Compare the DNS records a zone has with the records a team wants, and push the difference to the platform DNS
service.

## Records and changes (`dnsync/records.py`)

A `RecordSet` is `RecordSet(name, type, values, ttl=300)`: a name, a record type and a tuple of values that share one
TTL. A `Change` is `Change(action, record)` where `action` is `"create"`, `"update"` or `"delete"`.

### `plan_changes(current, desired) -> list[Change]`

Both arguments are lists of `RecordSet`.

- Record sets are matched on name and type. Names are compared case-insensitively and a single trailing dot is
  ignored (`WWW.Example.org.` is `www.example.org`). Types are compared case-insensitively.
- In `desired` only: `create`. In both, with a different set of values (order and surrounding whitespace do not
  matter) or a different TTL: `update` (the record of the change is the desired one). In `current` only: `delete`.
- `SOA` and `NS` record sets belong to the platform. They are ignored on both sides.
- The record inside every change is normalised: lowercase name without trailing dot, uppercase type, stripped
  values sorted alphabetically.
- The result lists all creates first, then updates, then deletes. Inside each group changes are sorted by name,
  then by type.
- Two record sets with the same name and type in one list raise `ValueError`.

### `change_payload(changes) -> dict`

The JSON body for the service: `{"changes": [{"action": ..., "name": ..., "type": ..., "ttl": ..., "values": [...]}]}`
in the same order as `changes`. Each entry takes the fields of `change.record` as they are; `values` is the tuple turned
into a list, in its stored order.

## API client (`dnsync/client.py`)

`DnsClient(token, base_url="https://dns.platform.internal/v2")` talks to the DNS service.

- A blank token raises `MissingCredentialsError`; surrounding whitespace is stripped from the token.
- `DnsClient.from_env(env=None)` reads the token from `DNS_API_TOKEN` (and optionally the base URL from
  `DNS_API_URL`). `env` defaults to `os.environ`. A missing or blank token raises `MissingCredentialsError`.
- `build_request(zone, changes)` returns a `urllib.request.Request`: `POST {base_url}/zones/{zone}/changes` with
  `change_payload(changes)` as the JSON body, the header `Authorization: Bearer <token>` and
  `Content-Type: application/json`. The zone is normalised like record names; a zone that does not have at least two
  labels made of letters, digits and inner hyphens raises `ValueError`.
- `push(zone, changes, *, timeout=10.0)` sends the request with `urllib.request.urlopen` and returns the decoded JSON
  answer. An empty change list returns `{"applied": 0}` without sending anything. Network failures and invalid
  answers raise `DnsError`.
