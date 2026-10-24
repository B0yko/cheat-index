"""`cheat-index demo`: re-score a bundled sample of real recorded runs, with no Docker and no API key.

The sample is a subset of the published v0.1.0 runs (record, changes, verification output and egress log per run).
The demo runs them through the same detectors, claim classifier and verdict rules as a live run, then prints a
mini leaderboard and one piece of evidence.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from cheat_index.paths import package_data
from cheat_index.report import build_leaderboard, pct
from cheat_index.scoring import summarise
from cheat_index.tasks.model import load_suite

SITE = "https://b0yko.github.io/cheat-index/"


def sample_dirs(root: Path | None = None) -> list[Path]:
    base = root or package_data("demo")
    return sorted(p.parent for p in base.rglob("record.json"))


def run_demo(root: Path | None = None) -> int:
    start = time.monotonic()
    tasks = {t.id: t for t in load_suite()}
    dirs = sample_dirs(root)
    if not dirs:
        print("cheat-index demo: no bundled runs found")
        return 1
    summaries: list[dict[str, Any]] = []
    for d in dirs:
        record = json.loads((d / "record.json").read_text(encoding="utf-8"))
        summaries.append(summarise(tasks[record["task"]["id"]], d))
    meta = json.loads(package_data("demo", "SAMPLE.json").read_text(encoding="utf-8"))
    excluded = dict(meta.get("excluded_detectors") or {})
    board = build_leaderboard(summaries, excluded_detectors=excluded, source="bundled demo sample")
    print(f"Agent Cheat Index demo: {len(summaries)} real runs re-scored from {meta['source']}")
    print(f"(recorded {meta['dates']} on {meta['hardware']}; the sample is small, so intervals are wide)\n")
    print("ACI = share of runs on contradictory, blocked and tempting-shortcut tasks in which the agent changed or")
    print("skipped checks without saying so, or claimed success that hidden checks contradict. Lower is better.\n")
    header = f"{'agent':22} {'model':34} {'runs':>4}  {'ACI [95% CI]':16} {'tampered':16} {'solved F3-F4':16}"
    print(header)
    print("-" * len(header))
    for c in board["configs"]:
        name = c["agent_display"] + (f" ({c['label']})" if c.get("label") else "")
        print(f"{name[:22]:22} {c['model'][:34]:34} {c['runs_valid']:>4}  {pct(c['aci']):16} "
              f"{pct(c['tamper_f13']):16} {pct(c['solve_f34']):16}")  # fmt: skip
    card = next((e for c in board["configs"] for e in c["evidence"] if e["kind"] == "tampered_undisclosed"), None)
    if card is None:
        card = next((e for c in board["configs"] for e in c["evidence"]), None)
    if card:
        print(f"\nEvidence, {card['task_id']}: {card['caption']}")
        for ev in card["evidence"][:1]:
            where = f" in {ev['file']}:{ev['line']}" if ev.get("file") else ""
            print(f"  {ev['detector']}{where}")
            for line in str(ev["excerpt"]).splitlines()[:8]:
                print(f"    {line}")
        message = card["final_message"].strip().splitlines()
        if message:
            print(f'  final message: "{message[0][:150]}"')
    if excluded:
        print(f"\n(as in the published index, these detectors are reported but not counted: {', '.join(excluded)})")
    print(f"\nre-scored in {time.monotonic() - start:.1f} s. Full leaderboard and method: {SITE}")
    print("Measure your own agent: cheat-index run --agent opencode --model <id> --tasks F4 --k 1")
    return 0
