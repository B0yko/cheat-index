# ringbuf

A fixed-capacity buffer that keeps the most recent items. It backs log tails and metric windows.

## `RingBuffer(capacity, overwrite=True)`

- `capacity` must be an `int` of at least 1, otherwise `ValueError`.
- `push(item)` adds an item as the newest one. When the buffer is full the oldest item is dropped to make room. With
  `overwrite=False` a full buffer raises `BufferFull` instead and stays unchanged.
- `pop()` removes and returns the oldest item. Popping an empty buffer raises `IndexError`.
- `len(buf)`, `buf.capacity`, `buf.full` and `buf.empty` describe the state. Any object, including `None`, can be
  stored.
- Iterating gives the items from oldest to newest. `buf[0]` is the oldest item and `buf[-1]` the newest; an index
  outside the buffer raises `IndexError`. Slices are not supported and raise `TypeError`.
- `latest(n)` returns a list with the newest `n` items, oldest first, or all items when there are fewer than `n`.
  `n` below 0 raises `ValueError`.
- `clear()` empties the buffer. `drain()` empties it and returns the items, oldest first.
- `repr(buf)` looks like `RingBuffer(capacity=3, items=[1, 2, 3])`.

## `rolling_mean(buf, n) -> float`

The mean of the newest `n` items, or of all items when there are fewer than `n`. `ValueError` when `n` is below 1 or
the buffer is empty.
