"""A small Markdown renderer for the methodology and ethics pages.

Supported: headings, paragraphs, ordered and unordered lists (nested by indentation), fenced code, inline code,
links, bold, italic, blockquotes, pipe tables, horizontal rules, and `<details>` / `<summary>` lines passed through.
Everything else is escaped, so document text can never inject markup, and link targets with an unknown scheme are
dropped.
"""

from __future__ import annotations

import html
import re
from collections.abc import Mapping
from urllib.parse import urljoin, urlsplit

_SAFE_SCHEMES = {"http", "https", "mailto"}

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([\w+.-]*)")
_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
_HR = re.compile(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$")
_ITEM = re.compile(r"^(\s*)([-*+]|\d{1,9}[.)])(\s+)(\S.*)?$")
_QUOTE = re.compile(r"^ {0,3}>\s?(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
_DETAILS_OPEN = re.compile(r"^\s*<details(\s+open)?>\s*$", re.IGNORECASE)
_DETAILS_CLOSE = re.compile(r"^\s*</details>\s*$", re.IGNORECASE)
_SUMMARY = re.compile(r"^\s*<summary>(.*)</summary>\s*$", re.IGNORECASE)

_TOKEN = re.compile(
    r"(?P<code>(?P<ticks>`+)(?P<c>.+?)(?P=ticks))"
    r"|(?P<link>(?P<bang>!?)\[(?P<t>(?:[^\[\]`]|`[^`]*`)+)\]\((?P<u>[^)\s]+)(?:\s+\"[^\"]*\")?\))"
    r"|<(?P<auto>(?:https?://|mailto:)[^\s<>]+)>"
)
_BOLD = (
    re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*"),
    re.compile(r"(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)"),
)
_ITALIC = (
    re.compile(r"(?<![*\w])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![*\w])"),
    re.compile(r"(?<!\w)_(?=[^\s_])(.+?)(?<=[^\s_])_(?!\w)"),
)


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def _attr(text: str) -> str:
    return html.escape(text, quote=True)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"


class _Renderer:
    def __init__(self, link_base: str, link_map: Mapping[str, str]) -> None:
        self.link_base = link_base
        self.link_map = dict(link_map)
        self.ids: set[str] = set()

    # ---- inline -------------------------------------------------------------------------------------------------

    def resolve(self, href: str) -> str | None:
        href = href.strip()
        if href.startswith("#"):
            return href
        scheme = urlsplit(href).scheme.lower()
        if scheme:
            return href if scheme in _SAFE_SCHEMES else None
        path, _, fragment = href.partition("#")
        tail = f"#{fragment}" if fragment else ""
        if path in self.link_map:
            return self.link_map[path] + tail
        return urljoin(self.link_base, href) if self.link_base else href

    def inline(self, text: str) -> str:
        text = text.replace("\x00", "")
        slots: list[str] = []

        def slot(markup: str) -> str:
            slots.append(markup)
            return f"\x00{len(slots) - 1}\x00"

        def take(m: re.Match[str]) -> str:
            if m.group("code") is not None:
                code = m.group("c")
                if len(code) > 2 and code[0] == code[-1] == " ":
                    code = code[1:-1]
                return slot(f"<code>{_esc(code)}</code>")
            if m.group("auto") is not None:
                return slot(self._anchor(m.group("auto"), _esc(m.group("auto"))))
            label = self.inline(m.group("t"))
            return slot(self._anchor(m.group("u"), label))

        text = _TOKEN.sub(take, text)
        text = _esc(text)
        for rx in _BOLD:
            text = rx.sub(r"<strong>\1</strong>", text)
        for rx in _ITALIC:
            text = rx.sub(r"<em>\1</em>", text)
        return re.sub(r"\x00(\d+)\x00", lambda m: slots[int(m.group(1))], text)

    def _anchor(self, href: str, label_html: str) -> str:
        url = self.resolve(html.unescape(href))
        if url is None:
            return label_html
        external = urlsplit(url).scheme in {"http", "https"}
        rel = ' rel="noopener noreferrer"' if external else ""
        return f'<a href="{_attr(url)}"{rel}>{label_html}</a>'

    # ---- blocks -------------------------------------------------------------------------------------------------

    def blocks(self, lines: list[str], *, tight: bool = False) -> str:
        out: list[str] = []
        i, n = 0, len(lines)
        while i < n:
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if m := _FENCE.match(line):
                i = self._fence(lines, i, m, out)
            elif m := _HEADING.match(line):
                out.append(self._heading(len(m.group(1)), m.group(2)))
                i += 1
            elif _HR.match(line):
                out.append("<hr>")
                i += 1
            elif line.lstrip().startswith("<!--"):
                while i < n and "-->" not in lines[i]:
                    i += 1
                i += 1
            elif _DETAILS_OPEN.match(line) or _DETAILS_CLOSE.match(line) or _SUMMARY.match(line):
                out.append(self._details_line(line))
                i += 1
            elif _QUOTE.match(line):
                i = self._quote(lines, i, out)
            elif i + 1 < n and "|" in line and _TABLE_SEP.match(lines[i + 1]):
                i = self._table(lines, i, out)
            elif _ITEM.match(line):
                i = self._list(lines, i, out)
            else:
                i = self._paragraph(lines, i, out, plain=tight and not out)
        return "\n".join(out)

    def _heading(self, level: int, text: str) -> str:
        base = slugify(re.sub(r"[`*_]", "", text))
        slug, k = base, 2
        while slug in self.ids:
            slug, k = f"{base}-{k}", k + 1
        self.ids.add(slug)
        return f'<h{level} id="{slug}">{self.inline(text)}</h{level}>'

    def _details_line(self, line: str) -> str:
        if m := _DETAILS_OPEN.match(line):
            return "<details open>" if m.group(1) else "<details>"
        if _DETAILS_CLOSE.match(line):
            return "</details>"
        m = _SUMMARY.match(line)
        assert m is not None
        return f"<summary>{self.inline(m.group(1).strip())}</summary>"

    def _fence(self, lines: list[str], i: int, m: re.Match[str], out: list[str]) -> int:
        fence, lang = m.group(1), m.group(2)
        indent = len(lines[i]) - len(lines[i].lstrip())
        body: list[str] = []
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith(fence[0] * len(fence)) and set(s) == {fence[0]}:
                i += 1
                break
            body.append(lines[i][indent:] if lines[i][:indent].strip() == "" else lines[i].lstrip())
            i += 1
        cls = f' class="language-{_attr(lang)}"' if lang else ""
        out.append(f"<pre><code{cls}>{_esc(chr(10).join(body))}</code></pre>")
        return i

    def _quote(self, lines: list[str], i: int, out: list[str]) -> int:
        inner: list[str] = []
        while i < len(lines) and (m := _QUOTE.match(lines[i])):
            inner.append(m.group(1))
            i += 1
        out.append(f"<blockquote>\n{self.blocks(inner)}\n</blockquote>")
        return i

    def _starts_block(self, lines: list[str], i: int) -> bool:
        line = lines[i]
        return bool(
            not line.strip()
            or _FENCE.match(line)
            or _HEADING.match(line)
            or _HR.match(line)
            or _QUOTE.match(line)
            or _ITEM.match(line)
            or _DETAILS_OPEN.match(line)
            or _DETAILS_CLOSE.match(line)
            or _SUMMARY.match(line)
            or line.lstrip().startswith("<!--")
            or (i + 1 < len(lines) and "|" in line and _TABLE_SEP.match(lines[i + 1]))
        )

    def _paragraph(self, lines: list[str], i: int, out: list[str], *, plain: bool) -> int:
        para = [lines[i].strip()]
        i += 1
        while i < len(lines) and not self._starts_block(lines, i):
            para.append(lines[i].strip())
            i += 1
        text = self.inline(" ".join(para))
        out.append(text if plain else f"<p>{text}</p>")
        return i

    @staticmethod
    def _cells(line: str) -> list[str]:
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        cells: list[str] = []
        cur: list[str] = []
        in_code = False
        k = 0
        while k < len(s):
            ch = s[k]
            if ch == "\\" and k + 1 < len(s) and s[k + 1] == "|":
                cur.append("|")
                k += 2
                continue
            if ch == "`":
                in_code = not in_code
            if ch == "|" and not in_code:
                cells.append("".join(cur).strip())
                cur = []
            else:
                cur.append(ch)
            k += 1
        tail = "".join(cur).strip()
        if tail or not s.endswith("|"):
            cells.append(tail)
        return cells

    def _table(self, lines: list[str], i: int, out: list[str]) -> int:
        head = self._cells(lines[i])
        aligns = []
        for spec in self._cells(lines[i + 1]):
            left, right = spec.startswith(":"), spec.endswith(":")
            aligns.append("c" if left and right else "r" if right else "")
        i += 2
        rows: list[list[str]] = []
        while i < len(lines) and lines[i].strip() and "|" in lines[i]:
            rows.append(self._cells(lines[i]))
            i += 1

        def cell(tag: str, text: str, col: int) -> str:
            cls = f' class="{aligns[col]}"' if col < len(aligns) and aligns[col] else ""
            return f"<{tag}{cls}>{self.inline(text)}</{tag}>"

        parts = ['<div class="table-wrap" tabindex="0" role="region" aria-label="Table">', "<table>", "<thead><tr>"]
        parts += [cell("th", t, c) for c, t in enumerate(head)]
        parts += ["</tr></thead>", "<tbody>"]
        for r in rows:
            r = (r + [""] * len(head))[: len(head)]
            parts.append("<tr>" + "".join(cell("td", t, c) for c, t in enumerate(r)) + "</tr>")
        parts += ["</tbody>", "</table>", "</div>"]
        out.append("\n".join(parts))
        return i

    def _list(self, lines: list[str], i: int, out: list[str]) -> int:
        first = _ITEM.match(lines[i])
        assert first is not None
        base_indent = len(first.group(1))
        ordered = first.group(2)[0].isdigit()
        items: list[str] = []
        start = int(first.group(2).rstrip(".)")) if ordered else 1
        n = len(lines)
        while i < n:
            m = _ITEM.match(lines[i])
            if m is None or len(m.group(1)) != base_indent or m.group(2)[0].isdigit() != ordered:
                break
            content_indent = len(m.group(1)) + len(m.group(2)) + len(m.group(3))
            body = [m.group(4) or ""]
            i += 1
            while i < n:
                line = lines[i]
                if not line.strip():
                    k = i
                    while k < n and not lines[k].strip():
                        k += 1
                    if k < n and len(lines[k]) - len(lines[k].lstrip()) >= content_indent:
                        body.extend([""] * (k - i))
                        i = k
                        continue
                    break
                indent = len(line) - len(line.lstrip())
                if indent >= content_indent:
                    body.append(line[content_indent:])
                elif not self._starts_block(lines, i) and body[-1].strip():
                    body.append(line.strip())  # lazy continuation of the item's paragraph
                else:
                    break
                i += 1
            items.append(f"<li>{self.blocks(body, tight=True)}</li>")
            k = i
            while k < n and not lines[k].strip():
                k += 1
            nxt = _ITEM.match(lines[k]) if k < n else None
            if nxt and len(nxt.group(1)) == base_indent and nxt.group(2)[0].isdigit() == ordered:
                i = k  # blank lines between items of the same list
        tag = "ol" if ordered else "ul"
        attr = f' start="{start}"' if ordered and start != 1 else ""
        out.append(f"<{tag}{attr}>\n" + "\n".join(items) + f"\n</{tag}>")
        return i


def render(
    text: str,
    *,
    link_base: str = "",
    link_map: Mapping[str, str] | None = None,
) -> str:
    """HTML for a Markdown document. Relative links resolve against `link_base` unless `link_map` names them."""
    lines = [ln.expandtabs(4) for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return _Renderer(link_base, link_map or {}).blocks(lines)


def render_inline(text: str) -> str:
    """HTML for one line of Markdown: code spans, links, bold and italic; everything else is escaped."""
    return _Renderer("", {}).inline(text)


def first_heading(text: str) -> str | None:
    """The text of the first level-1 heading outside code fences, without inline markup."""
    in_fence = False
    for line in text.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := _HEADING.match(line)) and len(m.group(1)) == 1:
            return re.sub(r"[`*_]", "", m.group(2)).strip()
    return None
