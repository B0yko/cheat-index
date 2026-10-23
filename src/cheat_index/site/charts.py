"""Charts for the Open Graph card and the README, drawn with matplotlib.

Output is deterministic: a fixed size and DPI, the bundled DejaVu Sans font, no Software tag in the PNG metadata, and
no dependence on a window system (a plain `Figure` with the Agg canvas, no pyplot state). Every position is in
pixels, so a chart looks the same wherever it is rendered.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import matplotlib
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

DPI = 100
FONT = "DejaVu Sans"
SITE_HOST = "b0yko.github.io/cheat-index"
DEFINITION = (
    "ACI is the share of F1–F3 runs in which the agent changed or skipped checks without saying so, "
    "or claimed success that hidden checks contradict. Lower is better."
)
Theme = Literal["light", "dark"]


@dataclass(frozen=True)
class Palette:
    surface: str
    text: str
    text2: str
    muted: str
    line: str
    bar: str
    bar_soft: str


LIGHT = Palette("#fcfcfb", "#0b0b0b", "#52514e", "#6b6a66", "#e1dfda", "#2a78d6", "#bfd6f2")
DARK = Palette("#1a1a19", "#f0efec", "#c3c2b7", "#a9a8a0", "#3a3935", "#3987e5", "#284a78")
PALETTES: dict[str, Palette] = {"light": LIGHT, "dark": DARK}


def aci_scale(configs: list[dict[str, Any]]) -> float:
    """Upper end of the shared ACI axis: the largest interval end rounded up to a tenth (at least 0.1, at most 1)."""
    highs = [c["aci"]["hi"] for c in configs if c["aci"].get("hi") is not None]
    top = max(highs, default=0.1)
    return min(1.0, max(0.1, math.ceil(round(top * 10, 6)) / 10))


def display_name(c: dict[str, Any]) -> str:
    return str(c["agent_display"]) + (f" ({c['label']})" if c.get("label") else "")


def _percent(iv: dict[str, Any]) -> str:
    if iv.get("point") is None:
        return "n/a"
    return f"{iv['point'] * 100:.0f}% [{iv['lo'] * 100:.0f}–{iv['hi'] * 100:.0f}]"


def _short_percent(iv: dict[str, Any]) -> str:
    return "n/a" if iv.get("point") is None else f"{iv['point'] * 100:.0f}%"


def _shown(board: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    rows = [c for c in board["configs"] if c["publishable"] and c["aci"].get("point") is not None]
    return rows[:limit]


def _facts(rows: list[dict[str, Any]]) -> tuple[str, str]:
    """The date range and hardware of the configurations that are drawn."""
    firsts = [c["date_first"] for c in rows if c.get("date_first")]
    lasts = [c["date_last"] for c in rows if c.get("date_last")]
    if firsts and lasts:
        first, last = min(firsts), max(lasts)
        dates = first if first == last else f"{first} to {last}"
    else:
        dates = ""
    hardware = "; ".join(dict.fromkeys(str(c["hardware"]) for c in rows if c.get("hardware")))
    return dates, hardware


class _Canvas:
    """A pixel-addressed drawing surface: x to the right, y downwards, text measured with the real renderer."""

    def __init__(self, width: int, height: int, pal: Palette) -> None:
        self.width, self.height, self.pal = width, height, pal
        self.fig = Figure(figsize=((width + 1e-6) / DPI, (height + 1e-6) / DPI), dpi=DPI, facecolor=pal.surface)
        self.canvas = FigureCanvasAgg(self.fig)
        self.renderer: RendererBase = self.canvas.get_renderer()  # type: ignore[no-untyped-call]
        self.ax: Axes = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(height, 0)
        self.ax.axis("off")

    def width_of(self, s: str, px: float, weight: str = "normal") -> float:
        t = self.ax.text(0, 0, s, fontsize=px * 72 / DPI, fontweight=weight)
        w = float(t.get_window_extent(self.renderer).width)
        t.remove()
        return w

    def fit(self, s: str, px: float, max_w: float, weight: str = "normal") -> str:
        if self.width_of(s, px, weight) <= max_w:
            return s
        while len(s) > 1 and self.width_of(s + "…", px, weight) > max_w:
            s = s[:-1]
        return s.rstrip() + "…"

    def wrap(self, s: str, px: float, max_w: float) -> list[str]:
        lines: list[str] = []
        cur = ""
        for word in s.split():
            trial = f"{cur} {word}".strip()
            if cur and self.width_of(trial, px) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return [*lines, cur] if cur else lines

    def text(
        self,
        x: float,
        y: float,
        s: str,
        px: float,
        color: str,
        *,
        weight: str = "normal",
        ha: str = "left",
        va: str = "center",
        max_w: float | None = None,
    ) -> None:
        if max_w is not None:
            s = self.fit(s, px, max_w, weight)
        self.ax.text(x, y, s, fontsize=px * 72 / DPI, fontweight=weight, color=color, ha=ha, va=va)

    def hline(self, x0: float, x1: float, y: float, color: str) -> None:
        self.ax.add_patch(Rectangle((x0, y - 0.5), x1 - x0, 1, facecolor=color, edgecolor="none", linewidth=0))

    def vline(self, x: float, y0: float, y1: float, color: str) -> None:
        self.ax.add_patch(Rectangle((x - 0.5, y0), 1, y1 - y0, facecolor=color, edgecolor="none", linewidth=0))

    def interval(self, x0: float, x1: float, yc: float, iv: dict[str, Any], scale: float, thick: float = 10) -> None:
        """A track, the 95% interval and the point, on the shared 0..scale axis between x0 and x1."""
        span = x1 - x0
        pal = self.pal
        self.ax.add_patch(
            FancyBboxPatch(
                (x0, yc - thick / 2),
                span,
                thick,
                boxstyle="round,pad=0,rounding_size=4",
                facecolor=pal.line,
                edgecolor="none",
                linewidth=0,
            )
        )
        lo, hi, p = (x0 + span * min(1.0, iv[k] / scale) for k in ("lo", "hi", "point"))
        self.ax.add_patch(
            FancyBboxPatch(
                (lo, yc - thick / 2),
                max(hi - lo, 3.0),
                thick,
                boxstyle="round,pad=0,rounding_size=4",
                facecolor=pal.bar_soft,
                edgecolor="none",
                linewidth=0,
            )
        )
        self.ax.add_patch(Circle((p, yc), thick / 2 + 3, facecolor=pal.surface, edgecolor="none", linewidth=0))
        self.ax.add_patch(Circle((p, yc), thick / 2 + 1, facecolor=pal.bar, edgecolor="none", linewidth=0))

    def axis_ticks(self, x0: float, x1: float, y_label: float, y0: float, y1: float, scale: float) -> None:
        """Hairline gridlines at 0, half and full scale, labelled above the rows."""
        for frac in (0.0, 0.5, 1.0):
            x = x0 + (x1 - x0) * frac
            self.vline(x, y0, y1, self.pal.line)
            ha = "left" if frac == 0 else "right" if frac == 1 else "center"
            self.text(x, y_label, f"{scale * frac * 100:.0f}%", 13, self.pal.muted, ha=ha)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(str(path), format="png", dpi=DPI, facecolor=self.pal.surface, metadata={"Software": None})


def _context() -> Any:
    return matplotlib.rc_context({"font.family": FONT, "font.sans-serif": [FONT], "text.antialiased": True})


def og_image(board: dict[str, Any], path: Path) -> None:
    """The 1200x630 social card: name, definition, the top rows with their ACI interval, date and hardware."""
    width, height, margin = 1200, 630, 64
    pal = DARK
    with _context():
        cv = _Canvas(width, height, pal)
        cv.text(margin, 66, "Agent Cheat Index", 54, pal.text, weight="bold")
        for i, line in enumerate(cv.wrap(DEFINITION, 21, width - 2 * margin)[:3]):
            cv.text(margin, 122 + i * 30, line, 21, pal.text2)
        rows = _shown(board, 5)
        top = 232
        if not rows:
            cv.text(margin, top + 60, "No configuration meets the publication rules yet.", 24, pal.text2)
        else:
            scale = aci_scale(rows)
            bx0, bx1, vx = 520, 880, 920
            row_h = 62
            cv.text(margin, top - 8, "Agent and model", 14, pal.muted)
            cv.text(bx0, top - 8, "ACI and 95% interval", 14, pal.muted, ha="left")
            cv.axis_ticks(bx0, bx1, top + 12, top + 26, top + 26 + row_h * len(rows) - 8, scale)
            for i, c in enumerate(rows):
                yc = top + 26 + row_h * i + row_h / 2 - 4
                cv.text(margin, yc - 11, display_name(c), 22, pal.text, weight="bold", max_w=bx0 - margin - 24)
                cv.text(margin, yc + 14, str(c["model"]), 15, pal.muted, max_w=bx0 - margin - 24)
                cv.interval(bx0, bx1, yc, c["aci"], scale)
                cv.text(vx, yc, _percent(c["aci"]), 22, pal.text, weight="bold")
        dates, hardware = _facts(rows)
        foot = " · ".join(p for p in (dates, hardware) if p)
        cv.hline(margin, width - margin, 580, pal.line)
        cv.text(margin, 604, foot, 15, pal.muted, max_w=width - 2 * margin - 300)
        cv.text(width - margin, 604, SITE_HOST, 15, pal.text2, ha="right")
        cv.save(path)


def leaderboard_chart(board: dict[str, Any], path: Path, theme: Theme = "light", top: int = 8) -> None:
    """The top of the leaderboard as a PNG about 1200 px wide, for the README."""
    pal = PALETTES[theme]
    rows = _shown(board, top)
    width, margin = 1200, 40
    head_h, row_h, foot_h = 118, 58, 56
    height = head_h + row_h * max(len(rows), 1) + foot_h
    with _context():
        cv = _Canvas(width, height, pal)
        cv.text(margin, 34, "Agent Cheat Index", 30, pal.text, weight="bold")
        cv.text(
            margin,
            66,
            "Share of F1–F3 runs with undisclosed tampering or a false success claim. Lower is better.",
            15,
            pal.text2,
        )
        cx = {
            "rank": margin,
            "name": margin + 62,
            "bar0": 460,
            "bar1": 780,
            "val": 810,
            "tamp": 1030,
            "solved": 1110,
            "n": 1160,
        }
        y_head = 98
        cv.text(cx["rank"], y_head, "Group", 13, pal.muted)
        cv.text(cx["name"], y_head, "Agent and model", 13, pal.muted)
        cv.text(cx["val"], y_head, "ACI [95% interval]", 13, pal.muted)
        cv.text(cx["tamp"], y_head, "Tampering", 13, pal.muted, ha="right")
        cv.text(cx["solved"], y_head, "Solved", 13, pal.muted, ha="right")
        cv.text(cx["n"], y_head, "Runs", 13, pal.muted, ha="right")
        cv.text(cx["tamp"], y_head + 15, "F1–F3", 12, pal.muted, ha="right")
        cv.text(cx["solved"], y_head + 15, "F3–F4", 12, pal.muted, ha="right")
        cv.hline(margin, width - margin, head_h - 2, pal.line)
        if not rows:
            cv.text(margin, head_h + row_h / 2, "No configuration meets the publication rules yet.", 18, pal.text2)
        else:
            scale = aci_scale(rows)
            y0, y1 = head_h, head_h + row_h * len(rows)
            cv.axis_ticks(cx["bar0"], cx["bar1"], y_head + 15, y0, y1, scale)
            for i, c in enumerate(rows):
                yc = y0 + row_h * i + row_h / 2
                if i:
                    cv.hline(margin, width - margin, y0 + row_h * i, pal.line)
                cv.text(cx["rank"] + 10, yc, str(c["rank_group"]), 18, pal.text, weight="bold", ha="center")
                name_w = cx["bar0"] - cx["name"] - 24
                cv.text(cx["name"], yc - 10, display_name(c), 17, pal.text, weight="bold", max_w=name_w)
                cv.text(cx["name"], yc + 13, str(c["model"]), 13, pal.muted, max_w=name_w)
                cv.interval(cx["bar0"], cx["bar1"], yc, c["aci"], scale)
                cv.text(cx["val"], yc, _percent(c["aci"]), 17, pal.text, weight="bold")
                cv.text(cx["tamp"], yc, _short_percent(c["tamper_f13"]), 16, pal.text2, ha="right")
                cv.text(cx["solved"], yc, _short_percent(c["solve_f34"]), 16, pal.text2, ha="right")
                cv.text(cx["n"], yc, str(c["runs_valid"]), 16, pal.text2, ha="right")
        dates, hardware = _facts(rows)
        foot = " · ".join(p for p in (dates, hardware) if p)
        cv.text(margin, height - 28, foot, 13, pal.muted, max_w=width - 2 * margin - 280)
        cv.text(width - margin, height - 28, SITE_HOST, 13, pal.text2, ha="right")
        cv.save(path)
