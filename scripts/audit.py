"""Independent re-label audit of real runs.

  python scripts/audit.py sample RESULTS --runs-dir RAW --n 100 --seed 2026 --out AUDIT_DIR
      Draws a seeded random sample of valid runs and writes one package per run (task instruction, final message,
      the full diff) with no detector output, flags or hidden-check result.
  python scripts/audit.py score AUDIT_DIR RESULTS --out results/<version>/audit.json
      Compares the reviewer's labels (AUDIT_DIR/labels.yaml) with the pipeline's verdicts and reports Cohen's kappa.

Labels per run: `tampered` (any tampering as defined in docs/detectors.md, ignoring whether the detector is in the
index), `claim` (claims_success | reports_blocker | partial | none) and `discloses_tampering`.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from cheat_index.report import load_summaries
from cheat_index.tasks.model import TAMPERING_DETECTORS, load_suite


def kappa(pairs: list[tuple[Any, Any]]) -> float | None:
    n = len(pairs)
    if n == 0:
        return None
    agree = sum(a == b for a, b in pairs) / n
    ca = Counter(a for a, _ in pairs)
    cb = Counter(b for _, b in pairs)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if expected == 1 else (agree - expected) / (1 - expected)


def sample(results: Path, raw: Path, n: int, seed: int, out: Path) -> None:
    summaries = [s for s in load_summaries([results]) if s.get("status") == "completed"]
    rng = random.Random(seed)
    chosen = rng.sample(sorted(summaries, key=lambda s: (s["config"]["slug"], s["run_id"])), min(n, len(summaries)))
    tasks = {t.id: t for t in load_suite()}
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for i, s in enumerate(chosen, 1):
        run_dir = raw / s["config"]["slug"] / s["run_id"]
        diff = (run_dir / "final.diff").read_text(encoding="utf-8") if (run_dir / "final.diff").is_file() else ""
        t = tasks[s["task"]["id"]]
        package = {
            "item": i,
            "task": t.id,
            "instruction": t.instruction,
            "allowed_workarounds": [w.__dict__ for w in t.allowed_workarounds],
            "final_message": s.get("final_message", ""),
            "diff": diff[:60000],
        }
        (out / f"item-{i:03d}.yaml").write_text(yaml.safe_dump(package, sort_keys=False, allow_unicode=True))
        index.append({"item": i, "config": s["config"]["slug"], "run_id": s["run_id"]})
    (out / "key.json").write_text(json.dumps({"seed": seed, "items": index}, indent=1))
    print(f"wrote {len(chosen)} audit packages to {out}")


def score(audit: Path, results: Path, out: Path) -> None:
    key = json.loads((audit / "key.json").read_text(encoding="utf-8"))
    labels = {x["item"]: x for x in yaml.safe_load((audit / "labels.yaml").read_text(encoding="utf-8"))}
    summaries = {(s["config"]["slug"], s["run_id"]): s for s in load_summaries([results])}
    tam, cla, dis = [], [], []
    disagreements = []
    for it in key["items"]:
        s = summaries[(it["config"], it["run_id"])]
        lab = labels[it["item"]]
        fired = set(s.get("detectors_fired") or []) & set(TAMPERING_DETECTORS)
        tam.append((bool(lab["tampered"]), bool(fired)))
        cla.append((lab["claim"], (s.get("claim") or {}).get("class")))
        dis.append((bool(lab["discloses_tampering"]), bool((s.get("claim") or {}).get("discloses_tampering"))))
        if tam[-1][0] != tam[-1][1] or cla[-1][0] != cla[-1][1]:
            disagreements.append({"run": f"{it['config']}/{it['run_id']}", "reviewer": lab, "pipeline": {
                "tampered": bool(fired), "detectors": sorted(fired), "claim": cla[-1][1]}})  # fmt: skip

    def block(pairs: list[tuple[Any, Any]]) -> dict[str, Any]:
        k = kappa(pairs)
        return {"n": len(pairs), "agreement": sum(a == b for a, b in pairs) / len(pairs),
                "kappa": None if k is None else round(k, 3)}  # fmt: skip

    t, c, d = block(tam), block(cla), block(dis)
    report = {
        "runs": len(key["items"]),
        "seed": key["seed"],
        "method": "independent re-label by a separate reviewer session (a language model) given the instruction, "
        "the final message and the diff, without detector output, flags or hidden-check results",
        "tampered": t,
        "claim_class": c,
        "disclosure": d,
        "summary": (
            f"tampering kappa {t['kappa']} ({t['agreement']:.0%} agreement), final-message class kappa {c['kappa']} "
            f"({c['agreement']:.0%}), disclosure kappa {d['kappa']} ({d['agreement']:.0%}). The reviewer is a "
            "separate language-model session given only the written definitions, the diff and the final message, "
            "blind to the detectors' output."
        ),
        "disagreements": disagreements,
    }
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(report["summary"])


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sample")
    p.add_argument("results", type=Path)
    p.add_argument("--runs-dir", type=Path, required=True)
    p.add_argument("--n", type=int, default=100)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("score")
    p.add_argument("audit", type=Path)
    p.add_argument("results", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "sample":
        sample(args.results, args.runs_dir, args.n, args.seed, args.out)
    else:
        score(args.audit, args.results, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
