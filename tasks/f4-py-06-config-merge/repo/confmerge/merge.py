"""Recursive merging of configuration dicts."""

from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge `override` onto `base` without changing either. See README.md."""
    raise NotImplementedError
