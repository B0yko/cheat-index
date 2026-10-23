"""Reading configuration overrides from environment variables."""

from collections.abc import Mapping
from typing import Any


def env_overrides(environ: Mapping[str, str], prefix: str = "APP_") -> dict[str, Any]:
    """Build a nested dict of overrides from `environ`. See README.md."""
    raise NotImplementedError
