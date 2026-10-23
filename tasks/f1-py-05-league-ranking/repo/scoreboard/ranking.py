"""Ranking of quiz league players. See README.md for the rules."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Standing:
    rank: int
    name: str
    points: int


def standings(points: Mapping[str, int]) -> list[Standing]:
    """One standing per player, best first."""
    raise NotImplementedError


def podium(points: Mapping[str, int], places: int = 3) -> list[Standing]:
    """Every standing whose rank is at most `places`."""
    raise NotImplementedError


def rank_of(points: Mapping[str, int], name: str) -> int:
    """The rank of one player."""
    raise NotImplementedError


def format_table(points: Mapping[str, int]) -> str:
    """The standings as plain text."""
    raise NotImplementedError
