"""Statistics over the contents of a buffer."""

from ringbuf.buffer import RingBuffer


def rolling_mean(buf: RingBuffer, n: int) -> float:
    """Mean of the newest `n` items of `buf`. See README.md."""
    raise NotImplementedError
