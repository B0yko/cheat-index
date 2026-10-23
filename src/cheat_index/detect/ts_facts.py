"""Runs `ts_assertions.cjs` (TypeScript compiler API) over changed TypeScript test files, before and after."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from cheat_index.detect.testfiles import TEST, classify
from cheat_index.diffing import diff_trees

SCRIPT = Path(__file__).with_name("ts_assertions.cjs")
TS_SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".mjs", ".cjs", ".jsx")


class TsFactsUnavailable(RuntimeError):
    """Node or the pinned `typescript` package is not available."""


@lru_cache(maxsize=1)
def _node_path() -> str:
    explicit = os.environ.get("CHEAT_INDEX_NODE_PATH")
    if explicit:
        return explicit
    npm = shutil.which("npm")
    if npm is None:
        return ""
    out = subprocess.run([npm, "root", "-g"], capture_output=True, text=True, check=False)
    return out.stdout.strip()


def analyse_sources(files: dict[str, str]) -> dict[str, Any]:
    node = shutil.which("node")
    if node is None:
        raise TsFactsUnavailable("node is not on PATH")
    env = dict(os.environ)
    env["NODE_PATH"] = _node_path()
    proc = subprocess.run(
        [node, str(SCRIPT)],
        input=json.dumps({"files": files}),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=120,
    )
    if proc.returncode != 0:
        raise TsFactsUnavailable(proc.stderr.strip()[-500:] or "ts_assertions.cjs failed")
    data: dict[str, Any] = json.loads(proc.stdout)
    return data


def collect_test_facts(start_dir: Path, final_dir: Path) -> dict[str, Any]:
    """Facts for every TypeScript/JavaScript test file the agent changed, deleted or added."""
    before: dict[str, str] = {}
    after: dict[str, str] = {}
    for ch in diff_trees(start_dir, final_dir):
        for path, text, bucket in ((ch.old_path, ch.old_text, before), (ch.path, ch.new_text, after)):
            if path and text is not None and path.endswith(TS_SUFFIXES) and classify(path) == TEST:
                bucket[path] = text
    if not before and not after:
        return {"typescript": None, "before": {}, "after": {}}
    b = analyse_sources(before) if before else {"files": {}}
    a = analyse_sources(after) if after else {"files": {}}
    return {
        "typescript": a.get("typescript") or b.get("typescript"),
        "before": b["files"],
        "after": a["files"],
    }
