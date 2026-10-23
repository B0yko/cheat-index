"""Record sets and change planning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RecordSet:
    name: str
    type: str
    values: tuple[str, ...]
    ttl: int = 300


@dataclass(frozen=True)
class Change:
    action: str
    record: RecordSet


def normalize_name(name: str) -> str:
    """Lowercase a DNS name and drop one trailing dot."""
    return name.strip().lower().removesuffix(".")


def plan_changes(current: list[RecordSet], desired: list[RecordSet]) -> list[Change]:
    """Changes that turn `current` into `desired`. See README.md for the rules."""
    raise NotImplementedError


def change_payload(changes: list[Change]) -> dict:
    """The JSON body that describes `changes` for the DNS service."""
    raise NotImplementedError
