"""Exceptions raised by the buffer."""


class BufferFull(Exception):
    """A full buffer that does not overwrite was asked to take another item."""
