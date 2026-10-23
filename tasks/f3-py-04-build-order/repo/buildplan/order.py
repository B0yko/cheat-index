"""Ordering of build targets."""

from collections.abc import Iterable, Mapping


class CycleError(Exception):
    """The dependencies contain a loop. `cycle` lists it, starting and ending with the same name."""

    def __init__(self, cycle: list[str]):
        super().__init__("dependency cycle: " + " -> ".join(cycle))
        self.cycle = cycle


def build_order(deps: Mapping[str, Iterable[str]]) -> list[str]:
    """Order the targets so that dependencies come first. See README.md for the rules."""
    raise NotImplementedError


def rebuild_set(deps: Mapping[str, Iterable[str]], changed: Iterable[str]) -> list[str]:
    """Targets to rebuild after `changed` changed, in build order. See README.md."""
    raise NotImplementedError
