"""Splitting money between parties."""

from collections.abc import Sequence


def allocate(total: int, weights: Sequence[int], caps: Sequence[int] | None = None) -> list[int]:
    """Split `total` cents in proportion to `weights`. See README.md for the rules."""
    raise NotImplementedError
