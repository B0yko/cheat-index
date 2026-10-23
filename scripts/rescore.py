"""Re-summarise every recorded run under the given directories with the current detectors and classifier.

Uses each run's recorded changes, verification output, egress log and final message; needs no containers.
Usage: python scripts/rescore.py RUNS_DIR [RUNS_DIR ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cheat_index.scoring import score_run_dir
from cheat_index.tasks.model import load_suite


def main(roots: list[str]) -> int:
    tasks = {t.id: t for t in load_suite()}
    n = 0
    for root in roots:
        for rec in sorted(Path(root).rglob("record.json")):
            if ".failed-" in str(rec):
                continue
            record = json.loads(rec.read_text(encoding="utf-8"))
            score_run_dir(tasks[record["task"]["id"]], rec.parent)
            n += 1
    print(f"re-scored {n} runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
