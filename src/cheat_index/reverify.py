"""`cheat-index verify RUN_DIR`: rebuild a run's end state from its recorded changes, verify and score it again,
and compare the result with the recorded summary."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from cheat_index.agents import get_adapter
from cheat_index.scoring import load_changes, load_proxy_log
from cheat_index.tasks.model import load_suite
from cheat_index.verdict import judge
from cheat_index.verification import verify


def rebuild_final(repo: Path, run_dir: Path, dest: Path) -> list[str]:
    """Task repository plus the recorded changes. Returns paths that could not be rebuilt (binary files)."""
    shutil.copytree(repo, dest)
    skipped = []
    for c in load_changes(run_dir):
        if c.status in ("deleted", "renamed") and c.old_path:
            (dest / c.old_path).unlink(missing_ok=True)
        if c.status != "deleted":
            if c.new_text is None:
                skipped.append(c.path)
                continue
            target = dest / c.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(c.new_text, encoding="utf-8")
    return skipped


def reverify(run_dir: Path) -> int:
    record = json.loads((run_dir / "record.json").read_text(encoding="utf-8"))
    tasks = {t.id: t for t in load_suite()}
    task = tasks[record["task"]["id"]]
    if task.content_hash() != record["task"]["content_hash"]:
        print(f"warning: task {task.id} changed since this run (content hash differs)")
    with tempfile.TemporaryDirectory(prefix="ci-reverify-") as tmp:
        final = Path(tmp) / "final"
        skipped = rebuild_final(task.repo_dir, run_dir, final)
        if skipped:
            print(f"warning: binary files not rebuilt: {skipped}")
        vr = verify(task, final)
    adapter = get_adapter(record["config"]["agent"])
    verdict = judge(task, load_changes(run_dir), vr, record.get("final_message", ""), load_proxy_log(run_dir),
                    adapter.harness_hosts)  # fmt: skip
    print(f"run {record['run_id']} ({record['config']['slug']})")
    print(f"visible tests: {'pass' if vr.visible.passed else 'fail'} {vr.visible.counts}")
    print(f"hidden checks: {'pass' if vr.hidden.passed else 'fail'} {vr.hidden.counts}")
    print(f"claim: {verdict.claim.cls} (discloses tampering: {verdict.claim.discloses_tampering})")
    print(f"detectors fired: {', '.join(verdict.fired) or 'none'}")
    print("flags: " + ", ".join(k for k, v in verdict.flags.items() if v))
    summary_file = run_dir / "summary.json"
    if summary_file.is_file():
        recorded = json.loads(summary_file.read_text(encoding="utf-8")).get("flags")
        same = recorded == verdict.flags
        print(f"matches recorded summary: {'yes' if same else 'NO'}")
        if not same:
            print(f"recorded flags: {recorded}")
            return 1
    return 0
