"""The ring buffer."""

from typing import Any


class RingBuffer:
    """Placeholder: keeps everything it is given, in order."""

    def __init__(self, capacity: int, overwrite: bool = True) -> None:
        self.capacity = capacity
        self.overwrite = overwrite
        self._items: list[Any] = []

    def push(self, item: Any) -> None:
        self._items.append(item)

    def __len__(self) -> int:
        return len(self._items)
