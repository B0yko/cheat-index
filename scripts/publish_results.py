"""Copy run summaries into results/<version>/ and pack raw runs into a release archive after a privacy scan.

Usage: python scripts/publish_results.py RUNS_DIR [RUNS_DIR ...] --version 0.1.0 [--archive dist/runs.tar.gz]

The scan fails (and nothing is written) if any file contains an OpenRouter key prefix, the tail of the key in
$OPENROUTER_API_KEY (if set), an absolute home path, or a private host name or address passed with --forbid.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_FILES = (
    "record.json",
    "summary.json",
    "stream.jsonl",
    "stderr.txt",
    "changes.json",
    "final.diff",
    "proxy.jsonl",
    "verify.json",
    "gateway.json",
)


def patterns(forbid: list[str]) -> list[re.Pattern[str]]:
    pats = [
        re.compile(r"sk-or-v1-[A-Za-z0-9]{8,}"),
        re.compile(r"/(?:Users|home)/(?!agent\b)[A-Za-z]"),
    ]
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if len(key) > 12:
        pats.append(re.compile(re.escape(key[-6:])))
    pats += [re.compile(re.escape(f)) for f in forbid]
    return pats


def scan(paths: list[Path], pats: list[re.Pattern[str]]) -> list[str]:
    problems = []
    for p in paths:
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat in pats:
            m = pat.search(text)
            if m:
                problems.append(f"{p}: matches {pat.pattern!r} near {text[max(0, m.start() - 30) : m.end() + 10]!r}")
    return problems


def run_dirs(roots: list[Path]) -> list[Path]:
    return sorted({s.parent for r in roots for s in r.rglob("summary.json") if ".failed-" not in str(s)})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--version", required=True)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--forbid", action="append", default=[], help="extra literal that must not appear")
    args = ap.parse_args()
    dirs = run_dirs(args.runs)
    errored = sorted({p.parent for r in args.runs for p in r.rglob("record.json")} - set(dirs))
    files = [d / f for d in dirs + errored for f in RAW_FILES if (d / f).is_file()]
    problems = scan(files, patterns(args.forbid))
    if problems:
        print("\n".join(problems[:50]), file=sys.stderr)
        return 1
    out = ROOT / "results" / args.version / "runs"
    if out.exists():
        shutil.rmtree(out)
    for d in dirs:
        summary = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        target = out / summary["config"]["slug"] / f"{summary['run_id']}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(dirs)} summaries to {out.relative_to(ROOT)}")
    if args.archive:
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(args.archive, "w:gz") as tar:
            for f in files:
                rel = f.relative_to(f.parents[2])
                info = tar.gettarinfo(f, arcname=f"cheat-index-{args.version}-runs/{rel.as_posix()}")
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = 0
                with f.open("rb") as fh:
                    tar.addfile(info, fh)
        print(f"wrote {args.archive} ({args.archive.stat().st_size / 1e6:.1f} MB, {len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
