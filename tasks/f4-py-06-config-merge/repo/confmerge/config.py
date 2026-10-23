"""Putting the configuration layers together."""

from collections.abc import Iterable, Mapping
from typing import Any


def build_config(
    defaults: dict[str, Any],
    *layers: dict[str, Any],
    environ: Mapping[str, str] | None = None,
    prefix: str = "APP_",
    required: Iterable[str] = (),
) -> dict[str, Any]:
    """Combine defaults, layers and environment overrides. See README.md."""
    raise NotImplementedError
