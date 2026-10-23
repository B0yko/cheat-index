"""Checks for single values."""

from rowcheck.schema import Column


def check_value(column: Column, raw: str) -> str | None:
    """Return a message when `raw` is not acceptable for `column`, otherwise None."""
    text = raw.strip()
    if text == "":
        return "is required" if column.required else None
    return None
