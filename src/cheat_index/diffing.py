"""Tree diffs between the state an agent started from and the state it left behind."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    ".tox",
    ".cache",
    ".npm",
}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
MAX_TEXT_BYTES = 512_000
RENAME_SIMILARITY = 0.6


@dataclass(frozen=True)
class FileChange:
    path: str
    status: str  # added | modified | deleted | renamed
    old_path: str | None
    old_text: str | None
    new_text: str | None
    binary: bool = False

    @property
    def any_path(self) -> str:
        return self.path


def _walk(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not root.is_dir():
        return out
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if p.is_file() and not p.is_symlink() and p.suffix not in IGNORED_SUFFIXES:
            out[rel.as_posix()] = p
    return out


def _read(p: Path) -> tuple[str | None, bool]:
    data = p.read_bytes()
    if len(data) > MAX_TEXT_BYTES or b"\0" in data[:8192]:
        return None, True
    try:
        return data.decode("utf-8"), False
    except UnicodeDecodeError:
        return None, True


def tree_files(root: Path) -> list[str]:
    return sorted(_walk(root))


def diff_trees(before: Path, after: Path) -> list[FileChange]:
    a, b = _walk(before), _walk(after)
    changes: list[FileChange] = []
    deleted: dict[str, tuple[str | None, bool]] = {}
    added: dict[str, tuple[str | None, bool]] = {}
    for rel in sorted(set(a) | set(b)):
        if rel in a and rel in b:
            if a[rel].read_bytes() != b[rel].read_bytes():
                ot, ob = _read(a[rel])
                nt, nb = _read(b[rel])
                changes.append(FileChange(rel, "modified", rel, ot, nt, ob or nb))
        elif rel in a:
            deleted[rel] = _read(a[rel])
        else:
            added[rel] = _read(b[rel])
    for new_rel in sorted(added):
        new_text, new_bin = added[new_rel]
        best, best_ratio = None, 0.0
        for old_rel, (old_text, old_bin) in deleted.items():
            if old_bin or new_bin or old_text is None or new_text is None:
                continue
            ratio = 1.0 if old_text == new_text else difflib.SequenceMatcher(None, old_text, new_text).ratio()
            if ratio > best_ratio:
                best, best_ratio = old_rel, ratio
        if best is not None and best_ratio >= RENAME_SIMILARITY:
            old_text, _ = deleted.pop(best)
            changes.append(FileChange(new_rel, "renamed", best, old_text, new_text))
        else:
            changes.append(FileChange(new_rel, "added", None, None, new_text, new_bin))
    for old_rel, (old_text, old_bin) in deleted.items():
        changes.append(FileChange(old_rel, "deleted", old_rel, old_text, None, old_bin))
    return sorted(changes, key=lambda c: c.path)


def unified(change: FileChange, context: int = 3) -> str:
    if change.binary:
        return f"Binary file {change.path} {change.status}\n"
    old = (change.old_text or "").splitlines(keepends=True)
    new = (change.new_text or "").splitlines(keepends=True)
    a = f"a/{change.old_path}" if change.old_path and change.status != "added" else "/dev/null"
    b = f"b/{change.path}" if change.status != "deleted" else "/dev/null"
    lines = list(difflib.unified_diff(old, new, a, b, n=context))
    return "".join(line if line.endswith("\n") else line + "\n" for line in lines)


def unified_all(changes: list[FileChange]) -> str:
    return "".join(unified(c) for c in changes)


def added_lines(change: FileChange) -> list[tuple[int, str]]:
    """(1-based line number in the new file, text) for every line the change adds."""
    if change.binary or change.new_text is None:
        return []
    old = (change.old_text or "").splitlines()
    new = change.new_text.splitlines()
    out: list[tuple[int, str]] = []
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            out.extend((j + 1, new[j]) for j in range(j1, j2))
    return out


def removed_lines(change: FileChange) -> list[tuple[int, str]]:
    if change.binary or change.old_text is None:
        return []
    old = change.old_text.splitlines()
    new = (change.new_text or "").splitlines()
    out: list[tuple[int, str]] = []
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for tag, i1, i2, _j1, _j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            out.extend((i + 1, old[i]) for i in range(i1, i2))
    return out


def hunk_for_line(change: FileChange, line_no: int, context: int = 3) -> str:
    """The unified-diff hunk that contains the given new-file line, for evidence excerpts."""
    text = unified(change, context)
    hunks: list[list[str]] = []
    for line in text.splitlines():
        if line.startswith("@@"):
            hunks.append([line])
        elif hunks:
            hunks[-1].append(line)
    header = text.splitlines()[:2]
    for h in hunks:
        try:
            spec = h[0].split("+")[1].split(" ")[0]
            start, _, length = spec.partition(",")
            s, n = int(start), int(length or "1")
        except (IndexError, ValueError):
            continue
        if s <= line_no <= s + max(n, 1) - 1 or n == 0:
            return "\n".join(header + h)
    return "\n".join(header + (hunks[0] if hunks else []))
