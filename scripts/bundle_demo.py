"""Copy a deterministic sample of real recorded runs into the package for `cheat-index demo`.

Usage: python scripts/bundle_demo.py RAW_RUNS_DIR --configs SLUG[,SLUG…] --per-config 12 [--version 0.1.0]

Per configuration it takes, in task-id order, the first runs of each family (so every family appears) and keeps
only what scoring reads: record.json (without the raw stream), changes.json, verify.json and proxy.jsonl.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "src" / "cheat_index" / "data" / "demo"


PRIVATE_IP = re.compile(r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b")


def copy_text(src: Path, dst: Path) -> None:
    """Copy as published: proxy logs without client addresses, private addresses replaced."""
    text = src.read_text(encoding="utf-8")
    if src.name == "proxy.jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip().startswith("{")]
        text = "".join(json.dumps({k: v for k, v in r.items() if k != "client"}) + "\n" for r in rows)
    dst.write_text(PRIVATE_IP.sub("<private-address>", text), encoding="utf-8")


def pick(config_dir: Path, per_config: int) -> list[Path]:
    runs = sorted(p.parent for p in config_dir.glob("*/record.json") if ".failed-" not in str(p))
    runs = [r for r in runs if json.loads((r / "record.json").read_text())["status"] == "completed"]
    by_family: dict[str, list[Path]] = {}
    for r in runs:
        by_family.setdefault(r.name[:2], []).append(r)
    chosen: list[Path] = []
    while len(chosen) < per_config and any(by_family.values()):
        for fam in sorted(by_family):
            if by_family[fam] and len(chosen) < per_config:
                chosen.append(by_family[fam].pop(0))
    return chosen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=Path)
    ap.add_argument("--configs", required=True)
    ap.add_argument("--per-config", type=int, default=12)
    ap.add_argument("--version", default="0.1.0")
    args = ap.parse_args()
    if DEST.exists():
        shutil.rmtree(DEST)
    dates, hardware, n = set(), set(), 0
    for slug in args.configs.split(","):
        for run in pick(args.raw / slug, args.per_config):
            out = DEST / slug / run.name
            out.mkdir(parents=True)
            record = json.loads((run / "record.json").read_text(encoding="utf-8"))
            dates.add(str(record.get("started_at", ""))[:10])
            hardware.add(record.get("hardware", ""))
            (out / "record.json").write_text(
                PRIVATE_IP.sub("<private-address>", json.dumps(record, indent=1)), encoding="utf-8"
            )
            verify = json.loads((run / "verify.json").read_text(encoding="utf-8"))
            for side in ("visible", "hidden"):
                verify[side]["output_tail"] = verify[side]["output_tail"][-800:]
            (out / "verify.json").write_text(
                PRIVATE_IP.sub("<private-address>", json.dumps(verify, indent=1)), encoding="utf-8"
            )
            copy_text(run / "changes.json", out / "changes.json")
            if (run / "proxy.jsonl").is_file():
                copy_text(run / "proxy.jsonl", out / "proxy.jsonl")
            n += 1
    meta = {
        "source": f"the published v{args.version} runs",
        "dates": " to ".join(sorted(d for d in dates if d)[:1] + sorted(d for d in dates if d)[-1:]),
        "hardware": ", ".join(sorted(h for h in hardware if h)),
        "runs": n,
    }
    (DEST / "SAMPLE.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    size = sum(p.stat().st_size for p in DEST.rglob("*") if p.is_file())
    print(f"bundled {n} runs into {DEST.relative_to(ROOT)} ({size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
