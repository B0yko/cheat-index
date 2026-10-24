"""Render .github/social-preview.png (1280x640) from the committed leaderboard.

The card is written as HTML (name, one-line value, headline numbers and a dot-and-interval chart of every published
configuration) and rendered with headless Chrome, which gives better type than matplotlib. Set CHROME to the browser
binary if it is not in the default place.

Usage: python scripts/social_preview.py [--version 0.1.0] [--html-only]
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from string import Template
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1280, 640
CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
    "chromium-browser",
)
MODELS = {
    "anthropic/claude-sonnet-5.5": "Sonnet 5.5",
    "anthropic/claude-haiku-5.5": "Haiku 5.5",
    "openai/gpt-5.3-codex": "GPT-5.3 Codex",
    "deepseek/deepseek-v4-flash": "DeepSeek V4 Flash",
    "qwen/qwen3-coder": "Qwen3 Coder",
    "z-ai/glm-5.3-flash": "GLM-5.3 Flash",
}
AGENTS = {"GitHub Copilot CLI": "Copilot CLI"}

# Chart geometry inside the card (px).
LABEL_W, PLOT_W, VALUE_W, ROW_H, GAP_H = 236, 262, 46, 31, 18

PAGE = Template(
    """<!doctype html>
<html><head><meta charset="utf-8"><style>
:root {
  --bg: #0d1117; --card: #151a23; --line: rgba(255, 255, 255, 0.08); --grid: rgba(255, 255, 255, 0.07);
  --text-1: #f3f4f6; --text-2: #c3c8d2; --text-3: #8b93a3; --series: #3987e5; --accent: #fbbf24;
}
* { box-sizing: border-box; margin: 0; }
html, body { width: ${width}px; height: ${height}px; overflow: hidden; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", "Segoe UI", Arial, sans-serif;
  color: var(--text-1); position: relative;
  background:
    radial-gradient(900px 520px at -8% -12%, rgba(57, 135, 229, 0.30), transparent 62%),
    radial-gradient(700px 420px at 112% 118%, rgba(251, 191, 36, 0.13), transparent 60%),
    var(--bg);
}
body::before {
  content: ""; position: absolute; inset: 0; opacity: 0.55;
  background-image: radial-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px); background-size: 22px 22px;
  -webkit-mask-image: linear-gradient(100deg, #000 0%, transparent 55%);
}
.left { position: absolute; left: 72px; top: 70px; width: 470px; }
.eyebrow {
  display: inline-block; padding: 6px 12px; border: 1px solid rgba(251, 191, 36, 0.45); border-radius: 999px;
  color: var(--accent); font-size: 14px; font-weight: 600; letter-spacing: 0.04em;
  background: rgba(251, 191, 36, 0.08);
}
h1 { margin-top: 22px; font-size: 62px; line-height: 1.02; font-weight: 800; letter-spacing: -0.025em; }
h1 span {
  background: linear-gradient(92deg, #fde68a, #fbbf24 45%, #f97316);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.tagline { margin-top: 20px; font-size: 23px; line-height: 1.36; color: var(--text-2); }
.tagline b { color: var(--text-1); font-weight: 600; }
.stats { display: flex; gap: 34px; margin-top: 36px; }
.stat b {
  display: block; font-size: 34px; font-weight: 700; letter-spacing: -0.02em; font-variant-numeric: tabular-nums;
}
.stat i { display: block; margin-top: 2px; font-style: normal; font-size: 14px; color: var(--text-3); }
.foot { position: absolute; left: 72px; bottom: 58px; width: 480px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  padding: 5px 11px; border-radius: 8px; border: 1px solid var(--line); background: rgba(255, 255, 255, 0.04);
  color: var(--text-2); font-size: 14px; font-weight: 500;
}
.url { margin-top: 14px; font-size: 16px; color: var(--text-3); letter-spacing: 0.01em; }
.url b { color: var(--text-1); font-weight: 600; }
.card {
  position: absolute; right: 64px; top: 56px; width: 612px; height: 528px; padding: 24px 26px 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0) 40%), var(--card);
  border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
}
.card h2 { font-size: 19px; font-weight: 700; letter-spacing: -0.01em; }
.card .sub { margin-top: 4px; font-size: 13px; color: var(--text-3); display: flex; align-items: center; gap: 8px; }
.key { display: inline-flex; align-items: center; gap: 6px; }
.key svg { display: block; }
.note {
  position: absolute; left: 26px; right: 26px; bottom: 16px; font-size: 12px; color: var(--text-3);
  display: flex; align-items: center; gap: 5px; white-space: nowrap;
}
svg text { font-family: inherit; }
</style></head>
<body>
<div class="left">
  <div class="eyebrow">Open benchmark · v${version}</div>
  <h1>Agent <span>Cheat</span> Index</h1>
  <p class="tagline">Your coding agent says <b>&ldquo;all tests pass&rdquo;</b>.<br>
    Did it fix the code, or the tests?</p>
  <div class="stats">
    <div class="stat"><b>${configs}</b><i>agent setups</i></div>
    <div class="stat"><b>${runs}</b><i>real runs</i></div>
    <div class="stat"><b>30</b><i>trap tasks + 10 controls</i></div>
  </div>
</div>
<div class="foot">
  <div class="chips">${chips}</div>
  <div class="url"><b>github.com/B0yko/cheat-index</b></div>
</div>
<div class="card">
  <h2>Flagged runs by agent and model</h2>
  <div class="sub">Trap-task runs with undisclosed test edits or a false &ldquo;done&rdquo; claim ·
    lower is better</div>
  ${chart}
  <div class="note"><span class="key"><svg width="30" height="12" viewBox="0 0 30 12"><line x1="2" y1="6" x2="28" y2="6"
    stroke="#3987e5" stroke-width="3" stroke-linecap="round" opacity="0.6"/><circle cx="15" cy="6" r="5" fill="#3987e5"
    stroke="#151a23" stroke-width="2"/></svg>95% interval</span> · dashed lines separate rank groups ·
    runs ${dates}</div>
</div>
</body></html>
"""
)


def _row_label(c: dict[str, Any]) -> str:
    agent = AGENTS.get(c["agent_display"], c["agent_display"]) + (" + rules" if c.get("label") == "rules" else "")
    model = MODELS.get(c["model"], c["model"].split("/")[-1])
    return f"{agent} · {model}"


def chart_svg(rows: list[dict[str, Any]]) -> str:
    """Dot-and-interval rows sorted by ACI, with a divider before each new rank group."""
    groups = sum(1 for i, c in enumerate(rows) if i and c["rank_group"] != rows[i - 1]["rank_group"])
    top, axis_h = 26, 22
    height = top + len(rows) * ROW_H + groups * GAP_H + axis_h
    width = LABEL_W + PLOT_W + VALUE_W

    def x(v: float) -> float:
        return LABEL_W + 8 + v * (PLOT_W - 16)

    parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="margin-top:14px">']
    plot_bottom = height - axis_h
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        parts.append(f'<line x1="{x(t):.1f}" y1="{top - 8}" x2="{x(t):.1f}" y2="{plot_bottom}" stroke="var(--grid)"/>')
        parts.append(f'<text x="{x(t):.1f}" y="{height - 4}" fill="var(--text-3)" font-size="12" '
                     f'text-anchor="middle">{t * 100:.0f}%</text>')  # fmt: skip
    y = top
    for i, c in enumerate(rows):
        if i and c["rank_group"] != rows[i - 1]["rank_group"]:
            mid = y + GAP_H / 2 - 4
            parts.append(f'<line x1="0" y1="{mid}" x2="{width}" y2="{mid}" stroke="rgba(255,255,255,0.14)" '
                         'stroke-dasharray="3 4"/>')  # fmt: skip
            y += GAP_H
        cy = y + ROW_H / 2 - 4
        aci = c["aci"]
        best_or_worst = i in (0, len(rows) - 1)
        parts.append(f'<text x="0" y="{cy + 4.5}" fill="var(--text-2)" font-size="13.5">'
                     f"{html.escape(_row_label(c))}</text>")  # fmt: skip
        parts.append(f'<line x1="{x(aci["lo"]):.1f}" y1="{cy}" x2="{x(aci["hi"]):.1f}" y2="{cy}" '
                     'stroke="var(--series)" stroke-width="3" stroke-linecap="round" opacity="0.6"/>')  # fmt: skip
        parts.append(f'<circle cx="{x(aci["point"]):.1f}" cy="{cy}" r="6.5" fill="var(--series)" '
                     'stroke="var(--card)" stroke-width="2"/>')  # fmt: skip
        weight = 700 if best_or_worst else 600
        parts.append(f'<text x="{width}" y="{cy + 4.5}" fill="var(--text-1)" font-size="14" font-weight="{weight}" '
                     f'text-anchor="end">{aci["point"] * 100:.0f}%</text>')  # fmt: skip
        y += ROW_H
    parts.append("</svg>")
    return "\n".join(parts)


def page(board: dict[str, Any]) -> str:
    rows = sorted((c for c in board["configs"] if c["publishable"]), key=lambda c: c["aci"]["point"])
    dates = sorted({d for c in rows for d in (c["date_first"], c["date_last"]) if d})
    span = f"{dates[0]} to {dates[-1][-2:]}" if len(dates) > 1 else (dates[0] if dates else "")
    agents = []
    for c in rows:
        name = AGENTS.get(c["agent_display"], c["agent_display"])
        if name not in agents:
            agents.append(name)
    return PAGE.substitute(
        width=WIDTH,
        height=HEIGHT,
        version=html.escape(board["version"]),
        configs=len(rows),
        runs=f"{sum(c['runs_valid'] for c in rows):,}",
        chips="".join(f'<span class="chip">{html.escape(a)}</span>' for a in agents),
        chart=chart_svg(rows),
        dates=html.escape(span),
    )


def chrome() -> str:
    for candidate in (os.environ.get("CHROME"), *CHROME_PATHS):
        if candidate and (Path(candidate).is_file() or shutil.which(candidate)):
            return candidate
    raise SystemExit("social_preview: no Chrome or Chromium found; set CHROME to the browser binary")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="0.1.0")
    ap.add_argument("--html-only", action="store_true", help="write the HTML next to the PNG and stop")
    args = ap.parse_args()
    board = json.loads((ROOT / "results" / f"v{args.version}" / "leaderboard.json").read_text(encoding="utf-8"))
    out = ROOT / ".github" / "social-preview.png"
    text = page(board)
    if args.html_only:
        out.with_suffix(".html").write_text(text, encoding="utf-8")
        print(f"wrote {out.with_suffix('.html').relative_to(ROOT)}")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "preview.html"
        src.write_text(text, encoding="utf-8")
        subprocess.run(
            [chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
             f"--window-size={WIDTH},{HEIGHT}", f"--screenshot={out}", src.as_uri()],
            check=True, capture_output=True, timeout=60,
        )  # fmt: skip
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
