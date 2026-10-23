# lrucache

A small in-memory cache with a size limit and optional expiry.

## `LRUCache(capacity, ttl=None, clock=time.monotonic)`

- `capacity` is the largest number of entries the cache keeps. It must be an `int` of at least 1, otherwise
  `ValueError`.
- `ttl` is how long an entry lives, in seconds, counted from the last `put` of its key. Reading an entry does not
  extend its life. An entry is expired once `clock() - stored_at >= ttl`. `None` means entries never expire; a `ttl`
  of zero or less raises `ValueError`.
- `clock` is a function returning the current time in seconds. Tests pass a fake one.

### Methods

- `put(key, value)` stores or replaces an entry, makes the key the most recently used and restarts its life. If the
  cache is now over capacity, expired entries are removed first; if it is still over capacity, the least recently
  used entries are evicted.
- `get(key, default=None)` returns the value and makes the key the most recently used. A missing or expired key gives
  `default`.
- `key in cache` is true only for live entries and does not change the order of use. `len(cache)` counts live entries.
- `pop(key, default=None)` removes an entry and returns its value, or `default` when it is missing or expired.
- `keys()` lists the live keys from least to most recently used.
- `get_or_load(key, loader)` returns the cached value, or calls `loader()` once, stores its result and returns it.
  The loader's result may be `None`. If the loader raises, nothing is stored.
- `clear()` removes every entry. The counters are kept.
- `stats()` returns `CacheStats(hits, misses, evictions)`. `get` and `get_or_load` each count exactly one hit or one
  miss per call. `evictions` counts live entries removed to make room; expired entries that are dropped do not count.
  `in`, `len`, `keys` and `pop` do not touch the counters.
