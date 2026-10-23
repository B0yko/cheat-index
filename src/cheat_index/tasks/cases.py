"""Labelled detector cases: patches against task repositories with expected detector labels.

`python -m cheat_index.tasks.cases FILE...` checks that every case names a known task, labels all detectors and
applies cleanly to a copy of the task repository.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from cheat_index.tasks.behaviour import Behaviour, BehaviourError, apply_changes, behaviour_from_dict
from cheat_index.tasks.model import DETECTORS, Task, Workaround, load_suite


@dataclass
class Case:
    id: str
    task_id: str
    labels: dict[str, bool]
    behaviour: Behaviour
    proxy_log: list[dict[str, Any]] = field(default_factory=list)
    workarounds: tuple[Workaround, ...] | None = None
    targets: tuple[str, ...] = ()
    note: str = ""


def load_cases(path: Path) -> list[Case]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    cases = []
    for raw in data:
        b = behaviour_from_dict(str(raw["id"]), {**raw, "kind": "cheat"})
        w = raw.get("allowed_workarounds")
        workarounds = (
            tuple(Workaround(str(x["detector"]), tuple(x.get("paths") or ()), str(x.get("note", ""))) for x in w)
            if w is not None
            else None
        )
        cases.append(
            Case(
                id=str(raw["id"]),
                task_id=str(raw["task"]),
                labels={k: bool(v) for k, v in (raw.get("labels") or {}).items()},
                behaviour=b,
                proxy_log=list(raw.get("commands_proxy_log") or []),
                workarounds=workarounds,
                targets=tuple(raw.get("targets") or ()),
                note=str(raw.get("note", "")),
            )
        )
    return cases


@contextmanager
def applied(task: Task, case: Case) -> Iterator[Path]:
    """A temporary copy of the task repository with the case's patch applied."""
    with tempfile.TemporaryDirectory(prefix="ci-case-") as tmp:
        final = Path(tmp) / "final"
        shutil.copytree(task.repo_dir, final)
        apply_changes(case.behaviour, final)
        yield final


def check(paths: list[Path]) -> int:
    tasks = {t.id: t for t in load_suite()}
    problems = 0
    for path in paths:
        cases = load_cases(path)
        seen: set[str] = set()
        for c in cases:
            issues = []
            if c.id in seen:
                issues.append("duplicate id")
            seen.add(c.id)
            if c.task_id not in tasks:
                issues.append(f"unknown task {c.task_id}")
            missing = set(DETECTORS) - set(c.labels)
            if missing:
                issues.append(f"labels missing {sorted(missing)}")
            if c.task_id in tasks:
                try:
                    with applied(tasks[c.task_id], c):
                        pass
                except BehaviourError as exc:
                    issues.append(str(exc))
            for i in issues:
                print(f"{path.name}:{c.id}: {i}")
            problems += bool(issues)
        pos = {d: sum(c.labels.get(d, False) for c in cases) for d in DETECTORS}
        print(f"{path}: {len(cases)} cases; positives per detector: {pos}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(check([Path(p) for p in sys.argv[1:]]))
