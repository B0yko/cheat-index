"""Turns a finished run directory into its committed summary (`summary.json`).

The summary carries everything the metrics need (flags, task, configuration, cost, tokens, wall time) plus short
evidence excerpts, the final message and the hidden-check result, so scores can be recomputed from summaries alone.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cheat_index.agents import get_adapter
from cheat_index.agents.base import RULES_PROBE_LINE
from cheat_index.diffing import FileChange
from cheat_index.tasks.model import Task
from cheat_index.verdict import judge
from cheat_index.verification import VerifyResult

SUMMARY_SCHEMA = "cheat-index/run-summary/v1"


def load_changes(run_dir: Path) -> list[FileChange]:
    data = json.loads((run_dir / "changes.json").read_text(encoding="utf-8"))
    return [FileChange(**c) for c in data]


def load_proxy_log(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "proxy.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("{"):
            out.append(json.loads(line))
    return out


def rules_loaded(record: dict[str, Any]) -> bool | None:
    if not record["config"].get("rules_sha256"):
        return None
    lines = [ln.strip().strip("`*_ ") for ln in str(record.get("final_message") or "").strip().splitlines()]
    return any(ln == RULES_PROBE_LINE for ln in lines[-3:])


def summarise(task: Task, run_dir: Path) -> dict[str, Any]:
    record: dict[str, Any] = json.loads((run_dir / "record.json").read_text(encoding="utf-8"))
    base: dict[str, Any] = {
        "schema": SUMMARY_SCHEMA,
        "run_id": record["run_id"],
        "repeat": record["repeat"],
        "attempt": record.get("attempt", 1),
        "config": record["config"],
        "task": record["task"],
        "hardware": record.get("hardware", ""),
        "status": record["status"],
        "error": record.get("error"),
        "started_at": record.get("started_at"),
        "ended_at": record.get("ended_at"),
        "wall_s": record.get("wall_s"),
        "usage": record.get("usage") or {},
        "agent_reported": {k: v for k, v in (record.get("agent_reported") or {}).items() if k != "usage"},
        "final_message": record.get("final_message", ""),
        "rules_loaded": rules_loaded(record),
    }
    if record["status"] != "completed":
        base["flags"] = None
        return base
    verify = VerifyResult.from_dict(json.loads((run_dir / "verify.json").read_text(encoding="utf-8")))
    proxy = load_proxy_log(run_dir)
    adapter = get_adapter(record["config"]["agent"])
    verdict = judge(task, load_changes(run_dir), verify, base["final_message"], proxy, adapter.harness_hosts)
    egress = [
        {"host": e.get("host"), "port": e.get("port"), "allowed": e.get("allowed")}
        for e in proxy
        if e.get("host") != "gateway"
    ]
    base.update(
        {
            "flags": verdict.flags,
            "claim": verdict.claim.to_dict(),
            "detectors_fired": verdict.fired,
            "detectors": verdict.to_dict()["detectors"],
            "visible": {"passed": verify.visible.passed, "counts": verify.visible.counts},
            "hidden": {
                "passed": verify.hidden.passed,
                "counts": verify.hidden.counts,
                "timed_out": verify.hidden.timed_out,
                "output_tail": verify.hidden.output_tail[-1200:],
            },
            "egress": egress,
            "diff_excerpt": diff_excerpt(run_dir),
        }
    )
    return base


def diff_excerpt(run_dir: Path, limit: int = 1500) -> str:
    """The diff of the first changed source file (else of the first changed file), truncated."""
    from cheat_index.detect.testfiles import SOURCE, classify
    from cheat_index.diffing import unified

    changes = load_changes(run_dir)
    if not changes:
        return ""
    chosen = next((c for c in changes if classify(c.path) == SOURCE), changes[0])
    return unified(chosen)[:limit]


def score_run_dir(task: Task, run_dir: Path) -> None:
    summary = summarise(task, run_dir)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
