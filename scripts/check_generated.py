"""Regenerate (or, with --check, verify) everything derived from the committed results.

Derived files: results/<version>/leaderboard.json, the generated blocks in README.md (between
`<!-- generated:NAME -->` and `<!-- /generated:NAME -->`), and the README leaderboard charts in docs/img/ (checked
through the sidecar docs/img/leaderboard-data.json, because PNG bytes depend on the platform's font rendering).

Usage: python scripts/check_generated.py [--check] [--version 0.1.0]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from cheat_index.report import build_leaderboard, load_summaries, markdown_table, ordered_statements, pct

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r"(<!-- generated:(?P<name>[\w-]+) -->\n)(?P<body>.*?)(<!-- /generated:(?P=name) -->)", re.DOTALL)


def load(version: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    results = ROOT / "results" / version
    quality_path = results / "quality.json"
    quality = json.loads(quality_path.read_text(encoding="utf-8")) if quality_path.is_file() else {}
    audit_path = results / "audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.is_file() else {}
    board = build_leaderboard(
        load_summaries([results / "runs"]),
        excluded_detectors=quality.get("excluded_from_index") or {},
        source=f"results/{version}",
    )
    return board, quality, audit


def _name(c: dict[str, Any]) -> str:
    return c["agent_display"] + (f" ({c['label']})" if c.get("label") else "")


def _pub(board: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in board["configs"] if c["publishable"]]


def block_headline(board: dict[str, Any]) -> str:
    pub = _pub(board)
    if not pub:
        return "No configuration has been published yet.\n"
    runs = sum(c["runs_valid"] for c in pub)
    lo = min(pub, key=lambda c: c["aci"]["point"])
    hi = max(pub, key=lambda c: c["aci"]["point"])
    dates = sorted({c["date_last"] for c in pub if c["date_last"]})
    return (
        f"Across {len(pub)} agent configurations and {runs} runs ({dates[-1] if dates else 'n/a'}, "
        f"{pub[0]['hardware']}), the Agent Cheat Index ranged from {pct(lo['aci'])} ({_name(lo)}, `{lo['model']}`) "
        f"to {pct(hi['aci'])} ({_name(hi)}, `{hi['model']}`): the share of runs on contradictory, blocked and "
        "tempting-shortcut tasks in which the agent changed or skipped checks without saying so, or claimed success "
        "that hidden checks contradict.\n"
    )


def block_leaderboard(board: dict[str, Any]) -> str:
    out = markdown_table(board)
    if board.get("excluded_detectors"):
        names = ", ".join(f"`{d}`" for d in board["excluded_detectors"])
        out += f"\nACI v{board['version']} is computed without {names}, which missed the detector release gates.\n"
    statements = ordered_statements(board)
    out += "\n" + (
        "\n".join(f"- {s}" for s in statements)
        if statements
        else "- No pair of configurations differs under the paired bootstrap rule; read the table as rank groups."
    )
    return out + "\n"


def _compare(board: dict[str, Any], rows: list[dict[str, Any]], title: str) -> str:
    if len(rows) < 2:
        return f"Not enough published configurations for the {title} comparison yet.\n"
    slugs = {c["slug"] for c in rows}
    lines = ["| Configuration | ACI [95% CI] | Tampering F1–F3 | False success | Honest stop F1–F2 | Solved F3–F4 |",
             "|---|---|---|---|---|---|"]  # fmt: skip
    for c in rows:
        lines.append(f"| {_name(c)}, `{c['model']}` | {pct(c['aci'])} | {pct(c['tamper_f13'])} | "
                     f"{pct(c['false_success'])} | {pct(c['honest_stop_f12'])} | {pct(c['solve_f34'])} |")  # fmt: skip
    pairs = [p for p in board["pairs"] if p["a"] in slugs and p["b"] in slugs]
    ordered = [p for p in pairs if p["ordered"]]
    overlap = all(
        a["aci"]["lo"] <= b["aci"]["hi"] and b["aci"]["lo"] <= a["aci"]["hi"] for a in rows for b in rows if a is not b
    )
    if ordered:
        lines.append("")
        lines.extend(f"- {s}" for s in ordered_statements({**board, "pairs": ordered}))
    else:
        lines.append("")
        lines.append(
            "- The ACI intervals "
            + ("overlap" if overlap else "do not all overlap, but no paired difference excludes zero")
            + f"; this sample does not show a {title} difference in ACI."
        )
    return "\n".join(lines) + "\n"


def block_harness(board: dict[str, Any]) -> str:
    pub = [c for c in _pub(board) if not c.get("rules") and not c.get("label")]
    by_model: dict[str, list[dict[str, Any]]] = {}
    for c in pub:
        by_model.setdefault(c["model"], []).append(c)
    model, rows = max(by_model.items(), key=lambda kv: len({c["agent"] for c in kv[1]}), default=("", []))
    return (f"Same model (`{model}`) in {len(rows)} harnesses:\n\n" if rows else "") + _compare(board, rows, "harness")


def block_models(board: dict[str, Any]) -> str:
    rows = [c for c in _pub(board) if c["agent"] == "opencode" and not c.get("rules") and not c.get("label")]
    return _compare(board, rows, "model")


def block_rules(board: dict[str, Any]) -> str:
    ruled = [c for c in _pub(board) if c.get("rules")]
    if not ruled:
        return "The rules experiment has not been published yet.\n"
    out = []
    for r in ruled:
        base = next((c for c in _pub(board) if c["agent"] == r["agent"] and c["model"] == r["model"]
                     and not c.get("rules") and not c.get("label")), None)  # fmt: skip
        if base is None:
            continue
        out.append(_compare(board, [base, r], "rules"))
        out.append(
            f"\nRuns excluded because the final message lacked the rules-loaded probe: {r['rules_not_loaded']}.\n"
        )
    return "\n".join(out) or "The rules experiment has no matching baseline.\n"


def block_families(board: dict[str, Any]) -> str:
    out = []
    for c in _pub(board):
        out.append(f"**{_name(c)}, `{c['model']}`**\n")
        out.append("| Family | Runs | Tampered | Undisclosed | False success | Honest stop | Solved |")
        out.append("|---|---|---|---|---|---|---|")
        for fam, m in c["per_family"].items():
            n = m["tampered"]["n"]
            cells = " | ".join(f"{m[f]['k']}/{n}" for f in ("tampered", "tampered_undisclosed", "false_success",
                                                            "honest_stop", "solved"))  # fmt: skip
            out.append(f"| {fam} | {n} | {cells} |")
        top = ", ".join(f"`{d}` ({k})" for d, k in c["top_tampering"][:4]) or "none"
        out.append(f"\nMost common tampering findings: {top}.\n")
    return "\n".join(out) + "\n"


def block_cost(board: dict[str, Any]) -> str:
    lines = ["| Configuration | Runs | Cost per run | Total cost | Tokens per run | Wall time per run |",
             "|---|---|---|---|---|---|"]  # fmt: skip
    for c in board["configs"]:
        lines.append(f"| {_name(c)}, `{c['model']}` | {c['runs_total']} | ${c['cost_per_run_usd']:.4f} | "
                     f"${c['cost_total_usd']:.2f} | {c['tokens_per_run']:,} | {c['wall_s_per_run']} s |")  # fmt: skip
    total = sum(c["cost_total_usd"] for c in board["configs"])
    lines.append(f"\nTotal for the published runs: ${total:.2f} (gateway-measured OpenRouter cost).")
    return "\n".join(lines) + "\n"


def block_quality(quality: dict[str, Any], audit: dict[str, Any]) -> str:
    if not quality:
        return "The detector quality report has not been generated yet.\n"

    def pr(m: dict[str, Any]) -> str:
        p, r = m["precision"], m["recall"]
        fp = "n/a" if p["point"] is None else f"{p['point']:.2f} [{p['lo']:.2f}–{p['hi']:.2f}]"
        fr = "n/a" if r["point"] is None else f"{r['point']:.2f} [{r['lo']:.2f}–{r['hi']:.2f}]"
        return f"{fp} | {fr}"

    a, h = quality["detectors"]["authored"], quality["detectors"]["heldout"]
    lines = [f"Detectors, on {a['cases']} authored and {h['cases']} frozen held-out labelled patches "
             "(precision and recall with Wilson 95% intervals):\n",
             "| Detector | Authored precision | Authored recall | Held-out precision | Held-out recall | In index |",
             "|---|---|---|---|---|---|"]  # fmt: skip
    excluded = quality.get("excluded_from_index") or {}
    for d in a["detectors"]:
        inside = "signal only" if d == "egress_attempt" else ("no" if d in excluded else "yes")
        lines.append(f"| `{d}` | {pr(a['detectors'][d])} | {pr(h['detectors'][d])} | {inside} |")
    ca, ch = quality["claims"]["authored"], quality["claims"]["heldout"]
    lines.append(
        f"\nFinal-message classifier: accuracy {ca['accuracy']['point']:.2f} on {ca['messages']} authored and "
        f"{ch['accuracy']['point']:.2f} [{ch['accuracy']['lo']:.2f}–{ch['accuracy']['hi']:.2f}] on {ch['messages']} "
        f"held-out messages; disclosure accuracy {ch['disclosure_accuracy']['point']:.2f} on the held-out set."
    )
    adj = quality.get("adjudication")
    if adj:
        lines.append(
            f"\nEvery held-out disagreement ({adj['disputed']['pairs']} detector/case pairs) was re-labelled blind "
            f"by a separate reviewer session (a language model given only the written definitions), mixed with "
            f"{adj['control']['pairs']} agreed controls: it upheld {adj['disputed']['upheld']} of "
            f"{adj['disputed']['pairs']} original labels and {adj['control']['upheld']} of {adj['control']['pairs']} "
            "controls, so the held-out numbers above stand ([details](eval/detectors/adjudication/README.md))."
        )
    if audit:
        lines.append(
            f"\nIndependent re-label agreement on {audit['runs']} randomly sampled real runs: {audit['summary']}"
        )
    return "\n".join(lines) + "\n"


def expected_blocks(board: dict[str, Any], quality: dict[str, Any], audit: dict[str, Any]) -> dict[str, str]:
    return {
        "headline": block_headline(board),
        "leaderboard": block_leaderboard(board),
        "harness": block_harness(board),
        "models": block_models(board),
        "rules": block_rules(board),
        "families": block_families(board),
        "cost": block_cost(board),
        "quality": block_quality(quality, audit),
    }


def chart_data(board: dict[str, Any]) -> dict[str, Any]:
    rows = [{"name": _name(c), "model": c["model"], "aci": c["aci"], "group": c["rank_group"]} for c in _pub(board)]
    blob = json.dumps(rows, sort_keys=True).encode()
    return {"sha256": hashlib.sha256(blob).hexdigest(), "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", default="0.1.0")
    args = ap.parse_args()
    board, quality, audit = load(args.version)
    problems: list[str] = []
    board_path = ROOT / "results" / args.version / "leaderboard.json"
    board_text = json.dumps(board, indent=1, ensure_ascii=False) + "\n"
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    blocks = expected_blocks(board, quality, audit)
    found = {m.group("name") for m in BLOCK.finditer(readme)}
    new_readme = BLOCK.sub(lambda m: m.group(1) + blocks.get(m.group("name"), m.group("body")) + m.group(4), readme)
    data_path = ROOT / "docs" / "img" / "leaderboard-data.json"
    data_text = json.dumps(chart_data(board), indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not board_path.is_file() or board_path.read_text(encoding="utf-8") != board_text:
            problems.append(f"{board_path.relative_to(ROOT)} is stale")
        if new_readme != readme:
            problems.append("README.md generated blocks are stale")
        missing = set(blocks) - found
        if missing:
            problems.append(f"README.md lacks generated blocks: {sorted(missing)}")
        if not data_path.is_file() or data_path.read_text(encoding="utf-8") != data_text:
            problems.append("README charts are stale (docs/img/leaderboard-data.json)")
        for p in problems:
            print(f"check_generated: {p}", file=sys.stderr)
        if not problems:
            print("generated files are up to date")
        return 1 if problems else 0
    from cheat_index.site.charts import leaderboard_chart

    board_path.write_text(board_text, encoding="utf-8")
    readme_path.write_text(new_readme, encoding="utf-8")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        leaderboard_chart(board, data_path.parent / f"leaderboard-{theme}.png", theme=theme)
    data_path.write_text(data_text, encoding="utf-8")
    print("regenerated leaderboard.json, README blocks and charts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
