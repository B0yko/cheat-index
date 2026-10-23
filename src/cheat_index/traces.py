"""Export runs as agent-trace/v1 (one JSON object per line) and import them back for re-scoring.

Steps come from the agent's stream (messages, tool calls, tool results; each tool_result right after its call),
followed by one `state_probe` step with the hidden-check result. When only a summary is available (the committed
results, without the raw stream), the trace carries just the final message and that probe step.
`meta.cheat_index` holds the run's configuration, detector findings, claim class and flags, so an imported trace
re-scores to the same numbers.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema

from cheat_index import __version__
from cheat_index.agents import get_adapter
from cheat_index.agents.base import Event
from cheat_index.paths import schemas_root

SOURCE = f"cheat-index/{__version__}"
CLAIM_TYPES = ("tests_passed", "done", "fixed", "blocked")


@lru_cache(maxsize=1)
def validator() -> jsonschema.Draft202012Validator:
    schema = json.loads((schemas_root() / "agent-trace-v1.json").read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def validate(trace: dict[str, Any]) -> None:
    errors = sorted(validator().iter_errors(trace), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        where = "/".join(str(p) for p in e.path) or "(root)"
        raise ValueError(f"agent-trace/v1 violation at {where}: {e.message}")


def _ordered(events: list[Event]) -> list[Event]:
    """Put every tool_result directly after the latest unanswered tool_call with the same name."""
    out: list[Event] = []
    orphans: list[Event] = []
    for e in events:
        if e.kind != "tool_result":
            out.append(e)
            continue
        for i in range(len(out) - 1, -1, -1):
            answered = i + 1 < len(out) and out[i + 1].kind == "tool_result"
            if out[i].kind == "tool_call" and out[i].name == e.name and not answered:
                out.insert(i + 1, e)
                break
        else:
            orphans.append(e)
    return out + orphans


def claim_types(summary: dict[str, Any]) -> list[dict[str, Any]]:
    claim = summary.get("claim") or {}
    cls = claim.get("class")
    if cls == "reports_blocker":
        return [{"type": "blocked", "subject": {"task": summary["task"]["id"]}}]
    if cls != "claims_success":
        return []
    signals = " ".join((claim.get("signals") or {}).get("success", [])).lower()
    types = []
    if any(w in signals for w in ("pass", "green", "succeed")):
        types.append("tests_passed")
    if "fixed" in signals:
        types.append("fixed")
    if not types or any(w in signals for w in ("done", "implement", "complete", "finished")):
        types.append("done")
    return [{"type": t, "subject": {"task": summary["task"]["id"]}} for t in types]


def build_trace(summary: dict[str, Any], instruction: str, events: list[Event] | None) -> dict[str, Any]:
    ts = str(summary.get("started_at") or "1970-01-01T00:00:00Z")
    end_ts = str(summary.get("ended_at") or ts)
    steps: list[dict[str, Any]] = [
        {"i": 0, "ts": ts, "kind": "message", "role": "user", "name": None, "content": instruction, "args": None,
         "ok": None, "output": None, "error": None}
    ]  # fmt: skip
    for e in _ordered(events or []):
        if e.kind == "message" and e.role == "user":
            continue
        steps.append(
            {
                "i": len(steps),
                "ts": e.ts or ts,
                "kind": e.kind,
                "role": e.role if e.kind != "tool_result" else "tool",
                "name": e.name if e.kind != "message" else None,
                "content": e.content if e.kind == "message" else None,
                "args": e.args if e.kind == "tool_call" else None,
                "ok": e.ok if e.kind == "tool_result" else None,
                "output": e.output if e.kind == "tool_result" else None,
                "error": e.error,
            }
        )
    hidden = summary.get("hidden") or {}
    steps.append(
        {"i": len(steps), "ts": end_ts, "kind": "state_probe", "role": "environment", "name": "hidden_checks",
         "content": None, "args": None, "ok": hidden.get("passed"), "output": {"counts": hidden.get("counts") or {}},
         "error": None}
    )  # fmt: skip
    completed = summary.get("status") == "completed"
    trace = {
        "schema": "agent-trace/v1",
        "trace_id": f"cheat-index/{summary['config']['slug']}/{summary['run_id']}",
        "source": SOURCE,
        "task": {"id": summary["task"]["id"], "domain": "coding", "instruction": instruction},
        "steps": steps,
        "final_claim": {"text": str(summary.get("final_message") or ""), "claims": claim_types(summary)},
        "ground_truth": (
            {
                "outcome": "success" if hidden.get("passed") else "failure",
                "checked_by": "state_probe",
                "details": {
                    "hidden_checks": {"passed": hidden.get("passed"), "counts": hidden.get("counts") or {}},
                    "visible_tests": summary.get("visible") or {},
                },
            }
            if completed
            else {"outcome": "unknown", "checked_by": "none"}
        ),
        "meta": {"cheat_index": {k: v for k, v in summary.items() if k not in ("final_message", "diff_excerpt")}},
    }
    validate(trace)
    return trace


def _events_for(run_dir: Path, agent: str) -> list[Event] | None:
    stream = run_dir / "stream.jsonl"
    if not stream.is_file():
        return None
    stderr = run_dir / "stderr.txt"
    adapter = get_adapter(agent)
    return adapter.parse(
        stream.read_text(encoding="utf-8", errors="replace"),
        stderr.read_text(encoding="utf-8", errors="replace") if stderr.is_file() else "",
    ).events


def export_traces(paths: Iterable[Path], out: Path) -> int:
    from cheat_index.report import load_summaries
    from cheat_index.tasks.model import load_suite

    instructions = {t.id: t.instruction for t in load_suite()}
    run_dirs: dict[tuple[str, str], Path] = {}
    for root in paths:
        if root.is_dir():
            for summary_file in root.rglob("summary.json"):
                d = summary_file.parent
                run_dirs[(d.parent.name, d.name)] = d
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for s in load_summaries(paths):
            run_dir = run_dirs.get((s["config"]["slug"], s["run_id"]))
            events = _events_for(run_dir, s["config"]["agent"]) if run_dir else None
            trace = build_trace(s, instructions.get(s["task"]["id"], ""), events)
            fh.write(json.dumps(trace, ensure_ascii=False) + "\n")
            n += 1
    return n


def read_traces(path: Path) -> Iterator[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            trace = json.loads(line)
            validate(trace)
            yield trace


def summaries_from_traces(path: Path) -> list[dict[str, Any]]:
    """Re-import exported traces as run summaries (for re-scoring)."""
    out = []
    for t in read_traces(path):
        s = dict(t["meta"]["cheat_index"])
        s["final_message"] = t["final_claim"]["text"]
        out.append(s)
    return out
