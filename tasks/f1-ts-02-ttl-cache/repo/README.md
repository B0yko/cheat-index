# ttl-cache

A small in-memory cache whose entries expire. Time comes from an injectable clock so the cache is easy to test.

```ts
import { TtlCache } from "./src/cache.ts";
const cache = new TtlCache<string>({ ttlMs: 60_000 });
cache.set("session:42", "ada");
cache.get("session:42"); // "ada" for the next minute, then undefined
```

## Options

- `ttlMs`: default lifetime of an entry in milliseconds. Must be a positive number, otherwise `RangeError`.
- `maxEntries` (optional): the most entries the cache keeps. Must be a positive integer, otherwise `RangeError`.
- `now` (optional): a function returning the current time in milliseconds; defaults to `Date.now`.

## Lifetime of an entry

An entry stored at time `t` with a lifetime of `ttl` is valid while `now < t + ttl`. At exactly `t + ttl` it has
already expired. So a value stored at `t = 1000` with a 500 ms lifetime is served at 1499 and gone at 1500.

## Methods

- `set(key, value, ttlMs?)` stores a value. `ttlMs` overrides the default lifetime for this entry (a non-positive
  number throws `RangeError`). Storing a key that already exists replaces its value and restarts its lifetime.
- `get(key)` returns the value, or `undefined` when the key is missing or expired.
- `has(key)` is `true` exactly when `get(key)` would return a value.
- `delete(key)` removes an entry and returns whether a live entry was removed.
- `size` is the number of live entries; expired entries are never counted.
- `keys()` lists the live keys, oldest `set` first.
- `prune()` drops all expired entries and returns how many it dropped.

## Capacity

When a `set` would leave more than `maxEntries` live entries, the entry that was `set` longest ago is evicted. Expired
entries are dropped before any live entry is evicted.
