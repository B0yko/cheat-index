"""Copy run summaries into results/<version>/ and pack raw runs into a release archive after a privacy scan.

Usage: python scripts/publish_results.py RUNS_DIR [RUNS_DIR ...] --version 0.1.0 [--archive dist/runs.tar.gz]

The scan fails (and nothing is written) if any file contains an OpenRouter key prefix, the tail of the key in
$OPENROUTER_API_KEY (if set), an absolute home path, or a private host name or address passed with --forbid.
"""

from __future__ import annotations

import argparse
import io
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
        PRIVATE_IP,
    ]
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if len(key) > 12:
        pats.append(re.compile(re.escape(key[-6:])))
    pats += [re.compile(re.escape(f)) for f in forbid]
    return pats


PRIVATE_IP = re.compile(r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b")


def published_text(p: Path) -> str:
    """The file as it is published: proxy logs lose the client's container address, and private network
    addresses (container bridges, the VM's resolver) that agents printed while probing are replaced."""
    text = p.read_text(encoding="utf-8", errors="replace")
    if p.name == "proxy.jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip().startswith("{")]
        text = "".join(json.dumps({k: v for k, v in r.items() if k != "client"}) + "\n" for r in rows)
    return PRIVATE_IP.sub("<private-address>", text)


def scan(paths: list[Path], pats: list[re.Pattern[str]]) -> list[str]:
    problems = []
    for p in paths:
        text = published_text(p)
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
        summary = json.loads(published_text(d / "summary.json"))
        target = out / summary["config"]["slug"] / f"{summary['run_id']}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(dirs)} summaries to {out.relative_to(ROOT)}")
    if args.archive:
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(args.archive, "w:gz") as tar:
            for f in files:
                rel = f.relative_to(f.parents[2])
                data = published_text(f).encode("utf-8")
                info = tarfile.TarInfo(f"cheat-index-{args.version}-runs/{rel.as_posix()}")
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                tar.addfile(info, io.BytesIO(data))
        print(f"wrote {args.archive} ({args.archive.stat().st_size / 1e6:.1f} MB, {len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
