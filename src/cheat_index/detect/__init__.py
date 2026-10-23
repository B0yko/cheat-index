"""Deterministic detectors over the diff between the start state and the end state (plus the egress log).

Every detector returns evidence (a file and line with an excerpt, or a log line), so each finding can be checked
by hand. Findings that a task's allowed workarounds cover are kept but marked `covered` and do not count.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Any

from cheat_index.diffing import FileChange
from cheat_index.tasks.model import DETECTORS, Task, Workaround


@dataclass
class Evidence:
    kind: str
    file: str | None = None
    line: int | None = None
    excerpt: str = ""
    covered: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "file": self.file, "line": self.line, "excerpt": self.excerpt[:600],
                "covered": self.covered}  # fmt: skip


@dataclass
class DetectorResult:
    name: str
    evidence: list[Evidence] = field(default_factory=list)
    unavailable: str | None = None

    @property
    def fired(self) -> bool:
        return any(not e.covered for e in self.evidence)

    @property
    def covered_only(self) -> bool:
        return bool(self.evidence) and not self.fired

    def to_dict(self) -> dict[str, Any]:
        return {
            "fired": self.fired,
            "covered": self.covered_only,
            "unavailable": self.unavailable,
            "evidence": [e.to_dict() for e in self.evidence[:5]],
        }


@dataclass
class DetectContext:
    task: Task
    changes: list[FileChange]
    test_facts: dict[str, Any] | None = None
    proxy_log: list[dict[str, Any]] = field(default_factory=list)
    harness_hosts: tuple[str, ...] = ()
    workarounds: tuple[Workaround, ...] | None = None

    @property
    def allowed(self) -> tuple[Workaround, ...]:
        return self.task.allowed_workarounds if self.workarounds is None else self.workarounds

    def covers(self, detector: str, path: str | None) -> bool:
        for w in self.allowed:
            if w.detector != detector:
                continue
            if not w.paths or (path is not None and any(fnmatch(path, p) for p in w.paths)):
                return True
        return False


Detector = Callable[[DetectContext], DetectorResult]
REGISTRY: dict[str, Detector] = {}


def register(name: str) -> Callable[[Detector], Detector]:
    def wrap(fn: Detector) -> Detector:
        REGISTRY[name] = fn
        return fn

    return wrap


def run_detectors(ctx: DetectContext) -> dict[str, DetectorResult]:
    _load()
    out: dict[str, DetectorResult] = {}
    for name in DETECTORS:
        fn = REGISTRY.get(name)
        if fn is None:
            out[name] = DetectorResult(name, unavailable="not implemented")
            continue
        result = fn(ctx)
        for ev in result.evidence:
            ev.covered = ev.covered or ctx.covers(name, ev.file)
        out[name] = result
    return out


def _load() -> None:
    """Import detector modules so they register themselves."""
    import importlib

    for module in ("rules",):
        name = f"cheat_index.detect.{module}"
        try:
            importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name != name:
                raise
