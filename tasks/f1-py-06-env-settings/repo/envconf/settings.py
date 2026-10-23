"""Typed access to environment-style settings. See README.md for the rules."""

from collections.abc import Iterable, Mapping

TRUE_WORDS = frozenset({"1", "true", "yes", "on"})
FALSE_WORDS = frozenset({"0", "false", "no", "off"})


class SettingError(ValueError):
    """A setting is present but cannot be used."""


def _raw(env: Mapping[str, str], key: str) -> str | None:
    """The stripped value of `key`, or None when the variable is unset."""
    raise NotImplementedError


def get_str(env: Mapping[str, str], key: str, default: str | None = None) -> str | None:
    """A text setting."""
    raise NotImplementedError


def get_bool(env: Mapping[str, str], key: str, default: bool = False) -> bool:
    """An on/off flag."""
    raise NotImplementedError


def get_int(
    env: Mapping[str, str],
    key: str,
    default: int | None = None,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    """A whole number, optionally within limits."""
    raise NotImplementedError


def get_list(env: Mapping[str, str], key: str, default: Iterable[str] = ()) -> list[str]:
    """A comma-separated list."""
    raise NotImplementedError
