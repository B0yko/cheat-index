"""Render .github/social-preview.png (1280x640) from the committed leaderboard: name, one-line value, headline.

Usage: python scripts/social_preview.py [--version 0.1.0]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="0.1.0")
    args = ap.parse_args()
    board = json.loads((ROOT / "results" / f"v{args.version}" / "leaderboard.json").read_text(encoding="utf-8"))
    pub = [c for c in board["configs"] if c["publishable"]]
    lo = min(c["aci"]["point"] for c in pub)
    hi = max(c["aci"]["point"] for c in pub)
    runs = sum(c["runs_valid"] for c in pub)
    fig = plt.figure(figsize=(12.8, 6.4), dpi=100)
    fig.patch.set_facecolor("#0f172a")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.06, 0.80, "Agent Cheat Index", color="#f8fafc", fontsize=54, fontweight="bold", va="center")
    ax.text(0.06, 0.66, "How often coding agents edit tests, special-case inputs\nor claim success they did not earn.",
            color="#cbd5e1", fontsize=24, va="center", linespacing=1.4)  # fmt: skip
    ax.text(0.06, 0.40, f"{lo * 100:.0f}% – {hi * 100:.0f}%", color="#fbbf24", fontsize=64, fontweight="bold",
            va="center")  # fmt: skip
    ax.text(0.06, 0.26, f"ACI range across {len(pub)} configurations, {runs} real runs, 30 trap tasks + 10 controls",
            color="#e2e8f0", fontsize=20, va="center")  # fmt: skip
    ax.text(0.06, 0.10, "Claude Code · Codex CLI · OpenCode · Copilot CLI   |   github.com/B0yko/cheat-index",
            color="#94a3b8", fontsize=17, va="center")  # fmt: skip
    out = ROOT / ".github" / "social-preview.png"
    fig.savefig(out, dpi=100, facecolor=fig.get_facecolor(), metadata={"Software": None})
    plt.close(fig)
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
