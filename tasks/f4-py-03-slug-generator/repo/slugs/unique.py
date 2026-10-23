"""Slugs that do not collide with existing ones."""

from collections.abc import Container


def unique_slug(text: str, taken: Container[str], max_length: int = 60) -> str:
    """Return a slug for `text` that is not in `taken`. See README.md for the rules."""
    raise NotImplementedError
