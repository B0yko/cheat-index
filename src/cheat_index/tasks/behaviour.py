"""Scripted behaviours: an honest end state or a cheating patch, written as file edits plus a final message.

The same format describes the detector evaluation cases, so one applier serves `tasks validate`, the labelled
sets and the scripted agent adapter.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


class BehaviourError(ValueError):
    """A behaviour cannot be loaded or applied."""


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str


@dataclass(frozen=True)
class Expect:
    visible_pass: bool | None = None
    hidden_pass: bool | None = None
    flags: tuple[str, ...] = ()
    not_flags: tuple[str, ...] = ()
    detectors: tuple[str, ...] = ()
    claim: str | None = None


@dataclass(frozen=True)
class Behaviour:
    name: str
    kind: str
    description: str
    final_message: str
    edits: tuple[Edit, ...] = ()
    write: dict[str, str] = field(default_factory=dict)
    delete: tuple[str, ...] = ()
    rename: tuple[tuple[str, str], ...] = ()
    commands: tuple[str, ...] = ()
    expect: Expect = field(default_factory=Expect)

    def to_payload(self) -> dict[str, Any]:
        """A JSON-safe form for the scripted agent (no expectations, no canary)."""
        return {
            "name": self.name,
            "final_message": self.final_message,
            "edits": [{"path": e.path, "old": e.old, "new": e.new} for e in self.edits],
            "write": dict(self.write),
            "delete": list(self.delete),
            "rename": [list(r) for r in self.rename],
            "commands": list(self.commands),
        }


def _safe_rel(path: str) -> str:
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise BehaviourError(f"unsafe path {path!r}")
    return p.as_posix()


def behaviour_from_dict(name: str, data: dict[str, Any]) -> Behaviour:
    kind = str(data.get("kind", ""))
    if kind not in ("honest", "cheat"):
        raise BehaviourError(f"{name}: kind must be honest or cheat")
    exp = data.get("expect") or {}
    expect = Expect(
        visible_pass=exp.get("visible_pass"),
        hidden_pass=exp.get("hidden_pass"),
        flags=tuple(exp.get("flags") or ()),
        not_flags=tuple(exp.get("not_flags") or ()),
        detectors=tuple(exp.get("detectors") or ()),
        claim=exp.get("claim"),
    )
    edits = tuple(Edit(_safe_rel(str(e["path"])), str(e["old"]), str(e["new"])) for e in data.get("edits") or ())
    write = {_safe_rel(str(k)): str(v) for k, v in (data.get("write") or {}).items()}
    delete = tuple(_safe_rel(str(p)) for p in data.get("delete") or ())
    rename = tuple((_safe_rel(str(r["from"])), _safe_rel(str(r["to"]))) for r in data.get("rename") or ())
    return Behaviour(
        name=name,
        kind=kind,
        description=str(data.get("description", "")).strip(),
        final_message=str(data.get("final_message", "")).strip(),
        edits=edits,
        write=write,
        delete=delete,
        rename=rename,
        commands=tuple(str(c) for c in data.get("commands") or ()),
        expect=expect,
    )


def load_behaviour(path: Path) -> Behaviour:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BehaviourError(f"{path}: expected a mapping")
    return behaviour_from_dict(path.stem, data)


def load_behaviours(directory: Path) -> list[Behaviour]:
    if not directory.is_dir():
        return []
    return [load_behaviour(p) for p in sorted(directory.glob("*.yaml"))]


def apply_changes(b: Behaviour, workdir: Path) -> None:
    """Apply renames, deletions, exact-substring edits and writes to a working copy, in that order."""
    for src, dst in b.rename:
        s, d = workdir / src, workdir / dst
        if not s.exists():
            raise BehaviourError(f"{b.name}: rename source {src} does not exist")
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(s, d)
    for rel in b.delete:
        p = workdir / rel
        if not p.exists():
            raise BehaviourError(f"{b.name}: cannot delete missing {rel}")
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
    for e in b.edits:
        p = workdir / e.path
        if not p.is_file():
            raise BehaviourError(f"{b.name}: edit target {e.path} does not exist")
        text = p.read_text(encoding="utf-8")
        count = text.count(e.old)
        if count != 1:
            raise BehaviourError(f"{b.name}: edit 'old' text occurs {count} times in {e.path} (needs exactly 1)")
        p.write_text(text.replace(e.old, e.new), encoding="utf-8")
    for rel, content in b.write.items():
        p = workdir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
