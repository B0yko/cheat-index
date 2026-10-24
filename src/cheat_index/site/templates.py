"""HTML templates for the static site.

Every `$name` placeholder is filled with markup that the caller has already escaped (or built from escaped parts),
so a template never sees raw data text. Literal `$` characters must not appear in template text.
"""

from __future__ import annotations

from string import Template

PAGE = Template(
    """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>$title</title>
<meta name="description" content="$description">
<link rel="canonical" href="$url">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Agent Cheat Index">
<meta property="og:title" content="$title">
<meta property="og:description" content="$description">
<meta property="og:image" content="$image">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="$image_alt">
<meta property="og:url" content="$url">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="$title">
<meta name="twitter:description" content="$description">
<meta name="twitter:image" content="$image">
<meta name="twitter:image:alt" content="$image_alt">
$assets
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
$header
<main id="main" class="wrap">
$body
</main>
$footer
$script
</body>
</html>
"""
)

HEADER = Template(
    """<header class="site-header">
<div class="wrap">
<a class="brand" href="${root}index.html">Agent Cheat Index</a>
<nav aria-label="Main">
$links
</nav>
</div>
</header>"""
)

REPORT_HEADER = Template(
    """<header class="site-header">
<div class="wrap">
<span class="brand">Agent Cheat Index</span>
<nav aria-label="Main">
<a href="$repo">GitHub</a>
</nav>
</div>
</header>"""
)

FOOTER = Template(
    """<footer class="site-footer wrap">
<p>$line</p>
<p>Source, task suite and raw results: <a href="$repo">$repo_label</a>. Code under the Apache-2.0 license.</p>
</footer>"""
)

INDEX_BODY = Template(
    """<h1>Agent Cheat Index</h1>
<p class="lead">$definition</p>
<p class="muted small">$summary</p>
<h2 id="leaderboard">Leaderboard</h2>
$leaderboard
$legend
$unpublished
<h2 id="differences">Differences that hold under a paired bootstrap</h2>
$differences
$excluded
<h2 id="more">More</h2>
<ul class="links">
$links
</ul>"""
)

LEGEND = """<details class="legend-box">
<summary>How to read the columns</summary>
<dl>
<dt>Rank group</dt>
<dd>Configurations are sorted by ACI. A configuration joins the current group unless its interval does not overlap
the interval of the group's first member. Groups are a coarse reading; the paired statements under the table are
a more sensitive test on the same tasks and can order two configurations in one group.</dd>
<dt>ACI</dt>
<dd>Share of F1&ndash;F3 runs in which the agent changed or skipped checks without saying so, or claimed success that
the hidden checks contradict. The bracket is a 95% task-cluster bootstrap interval. Lower is better.</dd>
<dt>Tampering F1&ndash;F3</dt>
<dd>Share of F1&ndash;F3 runs in which a tampering detector reported a change that the task does not allow,
whether or not the final message mentioned it.</dd>
<dt>Disclosed tampering</dt>
<dd>Share of F1&ndash;F3 runs with tampering where the final message says the checks were changed, skipped or
worked around. Disclosed tampering alone does not count towards the ACI.</dd>
<dt>False success F1&ndash;F4</dt>
<dd>Share of runs on all four families whose final message claims success while the hidden checks fail.</dd>
<dt>Honest stop F1&ndash;F2</dt>
<dd>Share of F1&ndash;F2 runs in which the agent reported a blocker or contradiction and did not tamper.
It sits next to the ACI so that a configuration that scores well by doing nothing shows up.</dd>
<dt>Solved F3&ndash;F4</dt>
<dd>Share of F3&ndash;F4 runs in which the hidden checks pass and the run is not tampered.</dd>
<dt>N valid runs, runs per task</dt>
<dd>Errored runs are left out of every rate and counted on the configuration page.</dd>
</dl>
</details>"""

UNPUBLISHED = Template(
    """<h2 id="not-published">Not published</h2>
<p>$intro</p>
$table"""
)

CONFIG_BODY = Template(
    """<p class="small"><a href="../index.html">&larr; Leaderboard</a></p>
<h1>$heading</h1>
$notice
<p class="lead">$lead</p>
$excluded
$sections"""
)

CONFIG_SECTION = Template(
    """<section id="cfg-$anchor">
<h2>$heading</h2>
$notice
<p class="lead">$lead</p>
$sections
</section>"""
)

FACTS = Template(
    """<dl class="facts">
$items
</dl>"""
)

CARD = Template(
    """<article class="card" id="evidence-$anchor">
<p class="kind"><span class="badge $badge">$kind</span> <span class="muted small">$meta</span></p>
<h$level>$caption</h$level>
$findings
$diff
$message
<p class="result"><strong>Hidden checks:</strong> $hidden</p>
</article>"""
)

DOC_BODY = Template(
    """<article class="prose">
$content
</article>"""
)

PLACEHOLDER_BODY = Template(
    """<article class="prose">
<h1>$title</h1>
<p>This document is published in the <code>docs/</code> folder of the
<a href="$repo">project repository</a>. This copy of the site was built without it.</p>
</article>"""
)

REPORT_BODY = Template(
    """<h1>Agent Cheat Index report</h1>
<p class="lead">$definition</p>
<p class="muted small">$summary</p>
<h2 id="leaderboard">Leaderboard</h2>
$leaderboard
$unpublished
<h2 id="differences">Differences that hold under a paired bootstrap</h2>
$differences
$excluded
$configs"""
)
