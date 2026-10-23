"""Column definitions and the problem records that the checks produce."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    kind: str = "text"
    required: bool = True
    choices: tuple[str, ...] = ()
    min_value: int | None = None
    max_value: int | None = None
    max_length: int | None = None


@dataclass(frozen=True)
class Problem:
    row: int
    column: str
    message: str
