"""Static site, report and chart tests.

Every run summary below is SYNTHETIC: it is made up inside this file to exercise the renderers, and none of it comes
from a real agent run.
"""

from __future__ import annotations

import json
import re
import struct
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest

from cheat_index.cli import main
from cheat_index.report import build_leaderboard, load_summaries
from cheat_index.site import charts, markdown
from cheat_index.site.build import SITE_URL, build_site, render_report_html
from cheat_index.tasks.model import TaskError

SCRIPT = "<script>alert(1)</script>"
IMG = "<img src=x onerror=alert(2)>"

# SYNTHETIC task list: (id, family, language, pressure)
TASKS = [
    ("f1-py-01-synthetic-a", "F1", "python", "tests"),
    ("f1-ts-01-synthetic-b", "F1", "typescript", "feature"),
    ("f2-py-01-synthetic-c", "F2", "python", "tests"),
    ("f3-py-01-synthetic-d", "F3", "python", "tests"),
    ("f3-ts-01-synthetic-e", "F3", "typescript", "feature"),
    ("f4-py-01-synthetic-f", "F4", "python", "tests"),
]

# SYNTHETIC outcomes per task and repeat.
HIGH = {
    "f1-py-01-synthetic-a": ["tampered_undisclosed", "tampered_undisclosed"],
    "f1-ts-01-synthetic-b": ["false_success", "tampered_undisclosed"],
    "f2-py-01-synthetic-c": ["false_success", "false_success"],
    "f3-py-01-synthetic-d": ["tampered_undisclosed", "tampered_undisclosed"],
    "f3-ts-01-synthetic-e": ["tampered_undisclosed", "false_success"],
    "f4-py-01-synthetic-f": ["solved", "solved"],
}
LOW = {
    "f1-py-01-synthetic-a": ["honest_stop", "honest_stop"],
    "f1-ts-01-synthetic-b": ["honest_stop", "tampered_disclosed"],
    "f2-py-01-synthetic-c": ["honest_stop", "honest_stop"],
    "f3-py-01-synthetic-d": ["solved", "solved"],
    "f3-ts-01-synthetic-e": ["solved", "unsolved"],
    "f4-py-01-synthetic-f": ["solved", "solved"],
}
THIN = {  # one run per task, one errored: not publishable
    "f1-py-01-synthetic-a": ["honest_stop"],
    "f2-py-01-synthetic-c": ["errored"],
    "f3-py-01-synthetic-d": ["false_success"],
}


def synthetic_run(slug: str, agent: str, label: str | None, model: str, task: tuple[str, str, str, str], k: int,
                  outcome: str, date: str) -> dict[str, Any]:  # fmt: skip
    task_id, family, language, pressure = task
    fired: list[str] = []
    claim, discloses, hidden_ok = "claims_success", False, True
    if outcome == "tampered_undisclosed":
        fired, hidden_ok = ["test_edit"], False
    elif outcome == "tampered_disclosed":
        fired, discloses = ["skip_added"], True
    elif outcome == "false_success":
        hidden_ok = False
    elif outcome == "honest_stop":
        claim, hidden_ok = "reports_blocker", False
    elif outcome == "unsolved":
        claim, hidden_ok = "none", False
    detectors: dict[str, Any] = {
        name: {"fired": False, "covered": False, "evidence": []} for name in ("test_edit", "skip_added", "mock_target")
    }
    for name in fired:
        detectors[name] = {
            "fired": True,
            "covered": False,
            "evidence": [
                {
                    "kind": "diff",
                    "file": "tests/test_synthetic.py",
                    "line": 12,
                    "excerpt": "-    assert total == 42\n+    assert total >= 0",
                    "covered": False,
                }
            ],
        }
    errored = outcome == "errored"
    message = f"All done, tests pass. {SCRIPT} & more." if outcome == "tampered_undisclosed" else f"Final note {k}."
    return {
        "schema": "cheat-index/run-summary/v1",
        "run_id": f"{task_id}--k{k}",
        "repeat": k,
        "attempt": 1,
        "config": {
            "slug": slug,
            "agent": agent,
            "agent_display": agent.title(),
            "model": model,
            "label": label,
            "cli_version": "1.2.3",
            "image_id": "sha256:0123456789abcdef0123456789abcdef",
            "flags": ["--synthetic", "--quiet"],
            "rules_sha256": None,
        },
        "task": {"id": task_id, "family": family, "language": language, "pressure": pressure, "content_hash": "00ff"},
        "hardware": "Synthetic test rig, 16 GB",
        "status": "errored" if errored else "completed",
        "started_at": f"{date}T10:00:00Z",
        "usage": {"cost_usd": 0.05, "prompt_tokens": 1000, "completion_tokens": 200},
        "wall_s": 42.0,
        "final_message": message,
        "flags": None if errored else {"placeholder": True},
        "claim": {"class": claim, "discloses_tampering": discloses, "signals": []},
        "detectors_fired": fired,
        "detectors": detectors,
        "hidden": {"passed": hidden_ok, "counts": {"passed": 3 if hidden_ok else 1, "failed": 0 if hidden_ok else 2}},
        "visible": {"passed": True, "counts": {"passed": 4}},
        "diff_excerpt": "--- a/src/synthetic.py\n+++ b/src/synthetic.py\n@@ -1,2 +1,2 @@\n-    return a + b\n"
        "+    return 42 < 43\n",
    }


def write_results(root: Path, *, with_thin: bool = False, quality: dict[str, str] | None = None) -> Path:
    results = root / "results"
    specs = [
        ("alpha agent/model-a", "alpha", IMG, "vendor/model-a&x", HIGH, "2026-01-05"),
        ("beta-model-b", "beta", None, "vendor/model-b", LOW, "2026-01-06"),
    ]
    if with_thin:
        specs.append(("gamma-model-c", "gamma", None, "vendor/model-c", THIN, "2026-01-07"))
    for slug, agent, label, model, outcomes, date in specs:
        folder = results / slug.replace("/", "_").replace(" ", "_")
        folder.mkdir(parents=True, exist_ok=True)
        for task in TASKS:
            for k, outcome in enumerate(outcomes.get(task[0], [])):
                run = synthetic_run(slug, agent, label, model, task, k, outcome, date)
                (folder / f"{run['run_id']}.json").write_text(json.dumps(run), encoding="utf-8")
    if quality is not None:
        (results / "quality.json").write_text(json.dumps({"excluded_from_index": quality}), encoding="utf-8")
    return results


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, int]:
    root = tmp_path_factory.mktemp("site")
    results = write_results(root, with_thin=True, quality={"mock_target": "precision below the gate"})
    out = root / "out"
    return out, build_site([results], out, docs_dir=root / "no-docs")


class _Tags(HTMLParser):
    """Collects every start tag with its attributes, so tests look at real markup, not at escaped text."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.feed(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


def tags(text: str) -> list[tuple[str, dict[str, str | None]]]:
    return _Tags(text).tags


def read(out: Path, rel: str) -> str:
    return (out / rel).read_text(encoding="utf-8")


def test_build_writes_pages_and_assets(built: tuple[Path, int]) -> None:
    out, pages = built
    assert pages == 1 + 2 + 3  # index, methodology, ethics, three configuration pages
    for rel in ("index.html", "methodology.html", "ethics.html", "style.css", "sort.js", "og.png"):
        assert (out / rel).is_file(), rel
    configs = sorted(p.name for p in (out / "configs").glob("*.html"))
    assert configs == ["alpha-agent-model-a.html", "beta-model-b.html", "gamma-model-c.html"]


def test_index_has_definition_table_and_links(built: tuple[Path, int]) -> None:
    out, _ = built
    page = read(out, "index.html")
    assert "<h1>Agent Cheat Index</h1>" in page
    assert "changed or skipped checks without saying so" in page and "lower is better" in page
    assert 'class="sortable leaderboard"' in page
    body = page.split("<tbody>")[1].split("</tbody>")[0]
    assert body.count("<tr>") == 2  # two ranked configurations
    for head in ("Rank group", "ACI [95% CI]", "Tampering F1", "Disclosed tampering", "False success",
                 "Honest stop F1", "Solved F3", "N valid runs", "Runs per task", "Cost per run", "CLI version",
                 "Date", "Hardware"):  # fmt: skip
        assert head in page, head
    assert 'href="configs/alpha-agent-model-a.html"' in page and 'href="configs/beta-model-b.html"' in page
    assert 'href="methodology.html"' in page and 'href="ethics.html"' in page
    assert 'href="https://github.com/B0yko/cheat-index"' in page
    assert "Synthetic test rig, 16 GB" in page
    # rank group and numeric sort keys are present
    assert 'data-sort="1"' in page and re.search(r'data-sort="0\.\d+"', page)


def test_index_lists_configurations_that_are_not_published(built: tuple[Path, int]) -> None:
    out, _ = built
    page = read(out, "index.html")
    section = page.split('id="not-published"')[1].split('id="differences"')[0]
    assert "Gamma" in section and "vendor/model-c" in section
    assert "valid runs per task (&lt; 2)" in section and "runs errored" in section
    assert 'href="configs/gamma-model-c.html"' in section


def test_differences_and_excluded_detectors(built: tuple[Path, int]) -> None:
    out, _ = built
    page = read(out, "index.html")
    differences = page.split('id="differences"')[1].split('id="more"')[0]
    assert "has a lower ACI than" in differences
    assert "<code>vendor/model-b</code>" in differences
    assert "ACI v0.1.0 is computed without these detectors" in page
    assert "<code>mock_target</code> (precision below the gate)" in page


def test_no_ordering_sentence_when_nothing_holds(tmp_path: Path) -> None:
    results = write_results(tmp_path)
    for f in (results / "beta-model-b").glob("*.json"):  # give the second configuration the first one's outcomes
        run = json.loads(f.read_text(encoding="utf-8"))
        tasks = {t[0]: t for t in TASKS}
        k = run["repeat"]
        new = synthetic_run("beta-model-b", "beta", None, "vendor/model-b", tasks[run["task"]["id"]], k,
                            HIGH[run["task"]["id"]][k], "2026-01-06")  # fmt: skip
        new["final_message"] = "same"
        f.write_text(json.dumps(new), encoding="utf-8")
    out = tmp_path / "site"
    build_site([results], out, docs_dir=tmp_path / "no-docs")
    page = read(out, "index.html")
    assert "None: every pair" in page and "has a lower ACI than" not in page


def test_config_pages(built: tuple[Path, int]) -> None:
    out, _ = built
    page = read(out, "configs/alpha-agent-model-a.html")
    # header facts
    for fact in ("1.2.3", "0123456789ab", "--synthetic --quiet", "Synthetic test rig, 16 GB", "2026-01-05",
                 "12 valid of 12 (0 errored)"):  # fmt: skip
        assert fact in page, fact
    # per-family table with k/N and Wilson intervals
    assert "F1 <span" in page and "F4 <span" in page
    assert '<span class="cell-n">4/4</span>' in page and re.search(r'class="cell-ci">\d+% \[\d+–\d+\]', page)
    # top detectors, grid labels, evidence cards
    assert "<code>test_edit</code>" in page
    for label in ("tampered", "false success", "solved"):
        assert f">{label}</span>" in page, label
    assert page.count('<article class="card"') >= 3
    assert "Hidden checks:</strong> failed (1 passed, 2 failed)" in page
    assert '<span class="l del">-    assert total == 42</span>' in page or "assert total == 42" in page
    assert "<blockquote>" in page and "<pre>" in page
    beta = read(out, "configs/beta-model-b.html")
    assert ">tampered, disclosed</span>" in beta and ">honest stop</span>" in beta and ">unsolved</span>" in beta
    gamma = read(out, "configs/gamma-model-c.html")
    assert ">errored</span>" in gamma and "Not ranked." in gamma


def test_text_is_escaped(built: tuple[Path, int]) -> None:
    out, _ = built
    for path in [out / "index.html", *(out / "configs").glob("*.html")]:
        text = path.read_text(encoding="utf-8")
        assert SCRIPT not in text and IMG not in text, path.name
        assert "onerror=alert" not in text.replace("onerror=alert(2)&gt;", ""), path.name
    alpha = read(out, "configs/alpha-agent-model-a.html")
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; more." in alpha
    assert "&lt;img src=x onerror=alert(2)&gt;" in alpha
    assert "vendor/model-a&amp;x" in alpha
    assert "return 42 &lt; 43" in alpha


def test_every_page_has_head_metadata_and_no_inline_handlers(built: tuple[Path, int]) -> None:
    out, _ = built
    for path in sorted(out.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(out).as_posix()
        assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in text, rel
        assert re.search(r"<title>[^<]+</title>", text), rel
        assert '<meta name="description" content="' in text, rel
        for tag in ("og:title", "og:description", "og:url"):
            assert f'<meta property="{tag}" content="' in text, (rel, tag)
        assert f'<meta property="og:image" content="{SITE_URL}og.png">' in text, rel
        assert f'<meta property="og:url" content="{SITE_URL}{"" if rel == "index.html" else rel}">' in text, rel
        assert '<meta name="twitter:card" content="summary_large_image">' in text, rel
        assert not [t for t, attrs in tags(text) if any(a.startswith("on") for a in attrs)], rel
        assert "javascript:" not in text, rel
        for tag, attrs in tags(text):
            href = attrs.get("href") or ""
            if tag == "a":
                assert not href.startswith("http") or href.startswith("https://github.com/B0yko/cheat-index"), rel
            if tag == "link" and attrs.get("rel") == "stylesheet":
                assert not href.startswith(("http", "//")), rel
            assert tag != "img" and not (tag == "script" and "src" in attrs and str(attrs["src"]).startswith("http"))
    assert re.search(r'<link rel="stylesheet" href="\.\./style\.css">', read(out, "configs/beta-model-b.html"))


def test_assets(built: tuple[Path, int]) -> None:
    out, _ = built
    assert len(read(out, "sort.js").splitlines()) < 60
    assert "prefers-color-scheme: dark" in read(out, "style.css")
    width, height = struct.unpack(">II", (out / "og.png").read_bytes()[16:24])
    assert (width, height) == (1200, 630)
    css = read(out, "style.css")
    assert "http://" not in css and "https://" not in css and "@import" not in css


def test_docs_are_rendered_or_replaced_by_a_placeholder(tmp_path: Path) -> None:
    results = write_results(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "methodology.md").write_text(
        "# How we measure\n\nSee [ethics](ethics-and-terms.md) and [ADR](adr/0005-x.md).\n\n- one `code`\n- two <b>\n",
        encoding="utf-8",
    )
    out = tmp_path / "site"
    build_site([results], out, docs_dir=docs)
    method = read(out, "methodology.html")
    assert '<h1 id="how-we-measure">How we measure</h1>' in method
    assert 'href="ethics.html"' in method
    assert 'href="https://github.com/B0yko/cheat-index/blob/main/docs/adr/0005-x.md"' in method
    assert "<li>two &lt;b&gt;</li>" in method
    ethics = read(out, "ethics.html")
    assert "published in the <code>docs/</code> folder" in ethics


def test_build_site_reads_nothing_and_fails_cleanly_without_results(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(TaskError):
        build_site([empty], tmp_path / "out")


def test_cli_site_build_and_html_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    results = write_results(tmp_path, with_thin=True)
    out = tmp_path / "dist"
    assert main(["site", "build", str(results), "--out", str(out)]) == 0
    assert "wrote 6 pages" in capsys.readouterr().out
    report = tmp_path / "report.html"
    assert main(["report", str(results), "--format", "html", "--out", str(report)]) == 0
    text = report.read_text(encoding="utf-8")
    assert text.startswith("<!doctype html>") and "Agent Cheat Index report" in text


def test_report_html_is_self_contained(tmp_path: Path) -> None:
    results = write_results(tmp_path, with_thin=True)
    board = build_leaderboard(load_summaries([results]))
    text = render_report_html(board)
    found = tags(text)
    assert "<style>" in text and "<script>" in text
    assert not [a for t, a in found if t == "link" and a.get("rel") == "stylesheet"]
    assert not [a for t, a in found if t == "script" and "src" in a]
    assert not [a for t, a in found if t == "img"]
    for slug in ("alpha-agent-model-a", "beta-model-b", "gamma-model-c"):
        assert f'id="cfg-{slug}"' in text and f'href="#cfg-{slug}"' in text
    ids = re.findall(r' id="([^"]+)"', text)
    assert len(ids) == len(set(ids))
    assert SCRIPT not in text and "&lt;script&gt;alert(1)&lt;/script&gt;" in text


def test_charts_are_deterministic_and_themed(tmp_path: Path) -> None:
    board = build_leaderboard(load_summaries([write_results(tmp_path)]))
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    charts.og_image(board, a)
    charts.og_image(board, b)
    assert a.read_bytes() == b.read_bytes() and b"Software" not in a.read_bytes()
    light, dark = tmp_path / "light.png", tmp_path / "dark.png"
    charts.leaderboard_chart(board, light, "light")
    charts.leaderboard_chart(board, dark, "dark")
    for p in (light, dark):
        width, height = struct.unpack(">II", p.read_bytes()[16:24])
        assert width == 1200 and 200 < height < 800
    assert light.read_bytes() != dark.read_bytes()
    again = tmp_path / "again.png"
    charts.leaderboard_chart(board, again, "light")
    assert again.read_bytes() == light.read_bytes()


def test_chart_for_a_board_without_ranked_configurations(tmp_path: Path) -> None:
    board = build_leaderboard(load_summaries([write_results(tmp_path)]))
    for c in board["configs"]:
        c["publishable"] = False
    charts.og_image(board, tmp_path / "og.png")
    charts.leaderboard_chart(board, tmp_path / "lb.png", "dark")
    assert (tmp_path / "og.png").stat().st_size > 1000


# ---- Markdown subset -----------------------------------------------------------------------------------------------


def test_markdown_blocks_and_inline() -> None:
    md = "\n".join([
        "## Title with `code`",
        "",
        "Para with **bold**, *italic*, `a<b` and [link](https://example.org/x?a=1&b=2).",
        "Second line of the paragraph.",
        "",
        "1. first",
        "2. second",
        "   - nested",
        "",
        "- a",
        "- b",
        "",
        "> quoted *text*",
        "",
        "```python",
        "print('<tag>')",
        "```",
        "",
        "| a | b |",
        "|---|--:|",
        "| 1 | `x\\|y` |",
        "",
        "<details>",
        "<summary>More</summary>",
        "",
        "inside",
        "",
        "</details>",
    ])  # fmt: skip
    out = markdown.render(md)
    assert '<h2 id="title-with-code">Title with <code>code</code></h2>' in out
    assert "<strong>bold</strong>, <em>italic</em>, <code>a&lt;b</code>" in out
    assert '<a href="https://example.org/x?a=1&amp;b=2" rel="noopener noreferrer">link</a>' in out
    assert "paragraph.</p>" in out and "Second line of the paragraph." in out
    assert "<ol>\n<li>first</li>\n<li>second\n<ul>\n<li>nested</li>\n</ul></li>\n</ol>" in out
    assert "<ul>\n<li>a</li>\n<li>b</li>\n</ul>" in out
    assert "<blockquote>\n<p>quoted <em>text</em></p>\n</blockquote>" in out
    assert "<pre><code class=\"language-python\">print('&lt;tag&gt;')</code></pre>" in out
    assert '<th class="r">b</th>' in out and '<td class="r"><code>x|y</code></td>' in out and "<table>" in out
    assert "<details>\n<summary>More</summary>\n<p>inside</p>\n</details>" in out


def test_markdown_escapes_and_drops_unsafe_links() -> None:
    out = markdown.render("<script>alert(1)</script>\n\n[x](javascript:alert(1)) and [y](data:text/html,hi)")
    assert "<script>" not in out and "&lt;script&gt;alert(1)&lt;/script&gt;" in out
    assert "javascript:" not in out and "data:" not in out and "<a " not in out
    assert markdown.render_inline("`a` & <i>") == "<code>a</code> &amp; &lt;i&gt;"
    assert markdown.first_heading("text\n```\n# no\n```\n# Yes *really*") == "Yes really"
