"""A least-recently-used cache with optional expiry."""

import time
from collections.abc import Callable, Hashable
from typing import Any

from lrucache.stats import CacheStats


class LRUCache:
    """Size-limited cache. See README.md for the rules."""

    def __init__(self, capacity: int, ttl: float | None = None, clock: Callable[[], float] = time.monotonic) -> None:
        raise NotImplementedError

    def put(self, key: Hashable, value: Any) -> None:
        raise NotImplementedError

    def get(self, key: Hashable, default: Any = None) -> Any:
        raise NotImplementedError

    def get_or_load(self, key: Hashable, loader: Callable[[], Any]) -> Any:
        raise NotImplementedError

    def pop(self, key: Hashable, default: Any = None) -> Any:
        raise NotImplementedError

    def keys(self) -> list[Hashable]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def stats(self) -> CacheStats:
        raise NotImplementedError

    def __contains__(self, key: Hashable) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
