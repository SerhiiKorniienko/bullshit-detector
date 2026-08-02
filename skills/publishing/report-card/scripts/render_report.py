#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Render a BS report (markdown) as a self-contained HTML report card.

Usage:
    uv run render_report.py <report.md> [-o out.html] [--og-image URL]

Output: one HTML file. Inline CSS, inline JS, no network requests, no fonts to
download. Opens in any browser, prints to a clean PDF, and reads on a phone —
which is where a shared link actually gets opened, and where the five-column
claims table in the markdown is unreadable.

Why a second parser exists when tally.py already reads the same table: they have
opposite jobs. tally.py is the gate — strict, exits 2, refuses to pass a report
whose arithmetic doesn't reconcile. This one is a viewer: it renders whatever it
is given and degrades to plain sections when a field is missing, because a
half-parsed report still beats no report. Do not make this one strict, and do not
make that one lenient.

This renders. It does not judge, recount, or add. Every number on the page comes
from the markdown verbatim.

Before rendering, the report is put through `tally.py` — the detector's compliance
gate. A page this presentable built from a report that fails its own arithmetic is
worse than no page: it launders a broken report into something that looks
authoritative. Rendering is refused unless the report passes, `--force` is given,
or the gate cannot be located.

Exit codes: 0 rendered · 1 bad input · 3 report failed the compliance gate.
"""

import argparse
import html
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Palette. Shared with share/scripts/render_carousel.py by copy, not by import:
# skills ship as independent directories in the plugin, so a cross-skill import
# would break the moment someone installs one without the other. Six constants
# are cheaper to keep in sync than that failure.
# ---------------------------------------------------------------------------

VERDICTS = {
    "confirmed":    ("✅", "#00FF00", "confirmed"),
    "plausible":    ("🟡", "#FFFF00", "plausible"),
    "misleading":   ("🟠", "#FF8800", "misleading"),
    "false":        ("❌", "#FF00FF", "false"),
    "unverifiable": ("❓", "#F5F5F5", "unverifiable"),
    "not checked":  ("⚪", "#FFFFFF", "not checked"),
}
GLYPH_TO_KEY = {glyph: key for key, (glyph, _, _) in VERDICTS.items()}

# RUBRIC.md "BS score (0–10)". Bands are the rubric's, not this script's.
SCORE_BANDS = [
    (2,  "Solid",           "#00FF00", "#000000"),
    (4,  "Mostly fine",     "#FFFF00", "#000000"),
    (6,  "Hype-heavy",      "#FF8800", "#000000"),
    (8,  "Mostly bullshit", "#FF00FF", "#000000"),
    (10, "Fabricated",      "#000000", "#FF00FF"),
]

# ---------------------------------------------------------------------------
# Header fields
# ---------------------------------------------------------------------------

H1 = re.compile(r"^#\s+(.+?)\s*$", re.M)
SOURCE_LINE = re.compile(r"^\*\*Source:\*\*\s*(.+?)\s*$", re.M)
CHECKED_LINE = re.compile(r"^\*\*Checked:\*\*\s*(.+?)\s*$", re.M)
# Em dash, en dash and hyphen all show up in real reports.
SCORE_LINE = re.compile(r"^\*\*BS score:\s*(\d+)\s*/\s*10\s*[—–-]\s*(.+?)\*\*\s*$", re.M)
TALLY_LINE = re.compile(r"^>?\s*\*\*Tally:\s*(.+?)$", re.M)
AMBIG_LINE = re.compile(r"^>?\s*\*\*Ambiguous:\s*(.+?)$", re.M)
RUN_LINE = re.compile(r"^\*(run:[^*]*)\*\s*$", re.M | re.I)
VERSION_STAMP = re.compile(r"bullshit-detector\s+v?(\d+\.\d+\.\d+|unknown)", re.I)
REPORT_PREFIX = re.compile(r"^BS Report:\s*")

# Claim numbers carry a letter suffix when a row splits late — the don't-merge rule
# turns row 24 into `24a` and `24b` rather than renumbering the table under it. A
# bare `\d+` silently dropped both halves, so a report with one split row rendered
# two claims short and lost a verdict bucket entirely: the published page showed
# 24 claims and no ❌ chip against a tally line reading 26 claims and 1 false.
# The page disagreeing with the report's own arithmetic is the one failure this
# tool cannot ship.
CLAIM_ROW = re.compile(r"^\|\s*(\d+[a-z]?)\s*\|")
TABLE_SEP = re.compile(r"^\|[\s:|-]+\|\s*$")


def classify(row: str) -> str | None:
    """Return a table row's verdict key, or None if it carries no verdict.

    Read the verdict *cell*, never the whole line. Evidence prose legitimately
    contains verdict glyphs — "Con 365 ✅; Labour won 202, not 203" sits in a 🟡
    row — and matching anywhere in the line silently promotes those to confirmed.
    Same bug, same fix as tally.py.
    """
    for cell in (c.strip() for c in row.split("|")):
        for glyph, key in GLYPH_TO_KEY.items():
            if cell.startswith(glyph):
                return key
    return None


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "-", s).strip("-") or "section"


# ---------------------------------------------------------------------------
# Inline markdown. Code spans are extracted first and restored last, so the
# brackets inside `[3 URLs → 1 origin: the round announcement]` are never read
# as a link.
# ---------------------------------------------------------------------------

CODE_SPAN = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
BARE_URL = re.compile(r"(?<![\"'=(>])\bhttps?://[^\s<>\"')\]]+")


def inline(text: str) -> str:
    codes: list[str] = []

    def stash(m: re.Match) -> str:
        codes.append(html.escape(m.group(1)))
        return f"\x00{len(codes) - 1}\x00"

    text = CODE_SPAN.sub(stash, text)
    text = html.escape(text)
    text = LINK.sub(
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}" '
                  f'rel="noopener noreferrer" target="_blank">{m.group(1)}</a>',
        text)
    text = BARE_URL.sub(
        lambda m: f'<a href="{m.group(0)}" rel="noopener noreferrer" '
                  f'target="_blank">{m.group(0)}</a>',
        text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = ITALIC.sub(r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)


# ---------------------------------------------------------------------------
# Block markdown. Deliberately small: reports are generated from one template,
# so this handles that template's shapes and passes anything else through as a
# paragraph rather than guessing.
# ---------------------------------------------------------------------------

TALLY_TOTAL = re.compile(r"(\d+)\s+claims?\s+extracted", re.I)
TALLY_BUCKET = re.compile(r"(\d+)\s+(confirmed|plausible|misleading|false|unverifiable)", re.I)


def reconcile_chips(claim_counter: dict, tally_match) -> None:
    """Say so when the filter chips disagree with the report's own tally line.

    The header of this file claims this script does not recount. That was never
    quite true — the chips are a recount, because the filters need a per-row verdict
    anyway — and the gap between the claim and the code is where a real defect hid:
    a `\\d+` row pattern dropped the `24a`/`24b` halves of a late-split row, so a
    published page showed 24 claims and no ❌ chip while the tally line under it read
    26 claims and 1 false.

    A viewer must not become a validator, so this refuses nothing and blocks nothing.
    It prints. A fact-checking tool publishing a page whose own two counts disagree is
    the failure that cannot be allowed to be silent — and silence is exactly what it
    was, until someone noticed the header numbers looked wrong.
    """
    if not tally_match:
        return
    text = tally_match.group(1)
    stated_total = TALLY_TOTAL.search(text)
    counted_total = sum(claim_counter.values())
    complaints = []
    if stated_total and int(stated_total.group(1)) != counted_total:
        complaints.append(f"tally line says {stated_total.group(1)} claims extracted, "
                          f"the rows on the page count {counted_total}")
    for found in TALLY_BUCKET.finditer(text):
        n, bucket = int(found.group(1)), found.group(2).lower()
        if claim_counter.get(bucket, 0) != n:
            complaints.append(f"tally line says {n} {bucket}, "
                              f"the rows count {claim_counter.get(bucket, 0)}")
    for c in complaints:
        print(f"warning: {c}", file=sys.stderr)
    if complaints:
        print("warning: the page and the report disagree — the row parser missed rows, "
              "or the tally line is stale. The markdown is the artifact; fix it there.",
              file=sys.stderr)


def render_blocks(lines: list[str], claim_counter: dict) -> str:
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            fence, i = [], i + 1
            while i < n and not lines[i].strip().startswith("```"):
                fence.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append(f"<pre><code>{chr(10).join(fence)}</code></pre>")
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            body = stripped.lstrip("#").strip()
            tag = f"h{min(level + 1, 6)}"
            out.append(f"<{tag}>{inline(body)}</{tag}>")
            i += 1
            continue

        if stripped.startswith("|"):
            table, start = [], i
            while i < n and lines[i].strip().startswith("|"):
                table.append(lines[i].strip())
                i += 1
            out.append(render_table(table, claim_counter))
            if i == start:
                i += 1
            continue

        if stripped.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
            continue

        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]).strip())
                i += 1
                # Fold continuation lines into the item they belong to.
                while (i < n and lines[i].strip()
                       and not re.match(r"^\s*[-*]\s+", lines[i])
                       and lines[i].startswith((" ", "\t"))):
                    items[-1] += " " + lines[i].strip()
                    i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]).strip())
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue

        para = []
        while i < n and lines[i].strip() and not lines[i].strip()[0] in "|>#-*`" \
                and not re.match(r"^\d+\.\s+", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        if not para:
            para = [stripped]
            i += 1
        text = " ".join(para)
        cls = ' class="callout"' if text.startswith("**") and text.rstrip().endswith("**") else ""
        out.append(f"<p{cls}>{inline(text)}</p>")

    return "\n".join(out)


def render_table(rows: list[str], claim_counter: dict) -> str:
    """Render a markdown table. Claim tables get per-row verdict metadata so the
    filter chips and the mobile card layout have something to work with."""
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows
             if not TABLE_SEP.match(r)]
    if not cells:
        return ""

    header, body = cells[0], cells[1:]
    is_claims = header and header[0].strip() in {"#", "No", "No."}

    thead = "".join(f"<th>{inline(h)}</th>" for h in header)
    trs = []
    for raw, row in zip((r for r in rows if not TABLE_SEP.match(r)), cells):
        if row is header:
            continue
        attrs, cls = "", ""
        if is_claims and CLAIM_ROW.match(raw):
            verdict = classify(raw)
            key = verdict or "not rateable"
            claim_counter[key] = claim_counter.get(key, 0) + 1
            attrs = f' data-verdict="{html.escape(key, quote=True)}"'
            # The verdict tint travels with the row as a custom property, so the
            # stylesheet needs one rule instead of one rule per verdict — and a
            # verdict added later cannot silently render as black-on-black.
            if verdict:
                attrs += f' style="--v:{VERDICTS[verdict][1]}"'
            cls = ' class="claim-row"'
        # Tag the verdict cell by content, not by column index — a report that
        # drops a column would otherwise paint the wrong one.
        tds = "".join(
            f'<td data-label="{html.escape(header[j] if j < len(header) else "", quote=True)}"'
            f'{" class=" + chr(34) + "verdict-cell" + chr(34) if cls and c[:1] in GLYPH_TO_KEY else ""}>'
            f"{inline(c)}</td>"
            for j, c in enumerate(row))
        trs.append(f"<tr{cls}{attrs}>{tds}</tr>")

    wrap_cls = "table-wrap claims" if is_claims else "table-wrap"
    return (f'<div class="{wrap_cls}"><table><thead><tr>{thead}</tr></thead>'
            f"<tbody>{''.join(trs)}</tbody></table></div>")


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------

def split_sections(body: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current_title is not None or current:
                sections.append((current_title or "", current))
            current_title, current = m.group(1), []
        else:
            current.append(line)
    sections.append((current_title or "", current))
    return sections


def score_band(score: int) -> tuple[str, str, str]:
    for ceiling, label, bg, fg in SCORE_BANDS:
        if score <= ceiling:
            return label, bg, fg
    return SCORE_BANDS[-1][1], SCORE_BANDS[-1][2], SCORE_BANDS[-1][3]


def strip_markdown(text: str) -> str:
    text = CODE_SPAN.sub(r"\1", text)
    text = LINK.sub(r"\1", text)
    text = BOLD.sub(r"\1", text)
    text = ITALIC.sub(r"\1", text)
    return text.strip()


def build(md: str, og_image: str | None) -> tuple[dict, str]:
    title_m = H1.search(md)
    title = title_m.group(1) if title_m else "BS Report"

    source_raw = (SOURCE_LINE.search(md).group(1) if SOURCE_LINE.search(md) else "")
    checked_raw = (CHECKED_LINE.search(md).group(1) if CHECKED_LINE.search(md) else "")
    score_m = SCORE_LINE.search(md)
    tally_m = TALLY_LINE.search(md)
    ambig_m = AMBIG_LINE.search(md)
    run_m = RUN_LINE.search(md)
    version_m = VERSION_STAMP.search(md)

    warnings = []
    for label, found in (("BS score", score_m), ("Source", source_raw),
                         ("version stamp", version_m), ("Tally", tally_m)):
        if not found:
            warnings.append(label)

    # Everything from the first "## " on is body. The header block above it is
    # re-rendered as the hero, so it must not appear twice.
    first_h2 = md.find("\n## ")
    body_md = md[first_h2:] if first_h2 != -1 else ""

    claim_counter: dict[str, int] = {}
    section_html = []
    claims_anchor = None
    for heading, lines in split_sections(body_md):
        if not heading and not any(l.strip() for l in lines):
            continue
        slug = slugify(heading)
        # The two sections a reader who scrolls to one place scrolls to.
        emphasis = ""
        if slug == "bottom-line":
            emphasis = " section--key"
        elif slug.startswith("what-a-hostile-reader"):
            emphasis = " section--key section--hostile"
        incidental = " section--incidental" if "incidental" in slug else ""
        before = len(claim_counter)
        inner = render_blocks(lines, claim_counter)
        if claims_anchor is None and (len(claim_counter) > before or claim_counter):
            claims_anchor = slug
        head = f'<h2 id="{slug}">{inline(heading)}</h2>' if heading else ""
        section_html.append(
            f'<section class="section{emphasis}{incidental}">{head}{inner}</section>')

    has_incidental = any("section--incidental" in s for s in section_html)

    # Hero
    if score_m:
        score = int(score_m.group(1))
        verdict_line = score_m.group(2).strip()
        band, bg, fg = score_band(score)
        hero_score = (
            f'<div class="score" style="background:{bg};color:{fg}">'
            f'<div class="score-num">{score}<span class="score-den">/10</span></div>'
            f'<div class="score-band">{html.escape(band)}</div></div>'
            f'<p class="score-verdict">{inline(verdict_line)}</p>')
        og_desc = strip_markdown(verdict_line)
        og_title = f"{strip_markdown(title)} — {score}/10"
    else:
        hero_score = '<div class="score score--none"><div class="score-num">—</div>' \
                     '<div class="score-band">no score</div></div>'
        og_desc = "BS report"
        og_title = strip_markdown(title)

    reconcile_chips(claim_counter, tally_m)

    chips = []
    present = [k for k in VERDICTS if claim_counter.get(k)]
    if present:
        total = sum(claim_counter.values())
        chips.append(f'<button class="chip chip--all is-on" data-filter="all">'
                     f'All <span class="n">{total}</span></button>')
        problems = claim_counter.get("false", 0) + claim_counter.get("misleading", 0)
        if problems:
            chips.append(f'<button class="chip chip--problems" data-filter="false misleading">'
                         f'Problems <span class="n">{problems}</span></button>')
        for key in present:
            glyph, colour, label = VERDICTS[key]
            chips.append(
                f'<button class="chip" data-filter="{key}" style="--chip:{colour}">'
                f'{glyph} {html.escape(label)} <span class="n">{claim_counter[key]}</span></button>')
    if has_incidental:
        chips.append('<button class="chip chip--lb" data-toggle="loadbearing">'
                     'Load-bearing only</button>')

    filters = (f'<nav class="filters" aria-label="Filter claims by verdict">'
               f'{"".join(chips)}</nav>') if chips else ""

    tally_html = ""
    if tally_m or ambig_m:
        parts = []
        if tally_m:
            parts.append(f'<p class="tally">{inline("**Tally: " + tally_m.group(1))}</p>')
        if ambig_m:
            parts.append(f'<p class="tally tally--ambig">'
                         f'{inline("**Ambiguous: " + ambig_m.group(1))}</p>')
        tally_html = f'<div class="tally-box">{"".join(parts)}</div>'

    run_html = (f'<p class="run">{html.escape(run_m.group(1))}</p>' if run_m else "")
    version = version_m.group(1) if version_m else "unknown"

    og_tags = (f'<meta property="og:image" content="{html.escape(og_image, quote=True)}">'
               f'<meta name="twitter:card" content="summary_large_image">'
               if og_image else '<meta name="twitter:card" content="summary">')

    # Backslashes are not allowed inside f-string expressions before 3.12, and
    # this file must run on 3.10.
    heading = inline(REPORT_PREFIX.sub("", title))

    warn_html = ""
    if warnings:
        warn_html = ('<p class="parse-warning">Rendered with missing header fields: '
                     + html.escape(", ".join(warnings))
                     + '. The markdown report is the source of truth.</p>')

    # Handed back so the caller can print a summary it did not have to remember.
    # Every figure here was recounted by tally.py moments ago; a summary rebuilt
    # from memory is wrong in the direction that flatters the run.
    meta = {
        "title": strip_markdown(REPORT_PREFIX.sub("", title)),
        "score": int(score_m.group(1)) if score_m else None,
        "band": score_band(int(score_m.group(1)))[0] if score_m else None,
        "verdict": strip_markdown(score_m.group(2)) if score_m else None,
        # Keep the opening `**` the regex ate, or the line's own closing one is
        # left unpaired and shows up as literal asterisks in the handoff.
        "tally": strip_markdown("**Tally: " + tally_m.group(1)) if tally_m else None,
        "ambiguous": strip_markdown("**Ambiguous: " + ambig_m.group(1)) if ambig_m else None,
        "run": run_m.group(1) if run_m else None,
        "version": version,
        "claims": dict(claim_counter),
        "missing": warnings,
    }

    return meta, f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(og_title)}</title>
<meta name="description" content="{html.escape(og_desc, quote=True)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(og_title, quote=True)}">
<meta property="og:description" content="{html.escape(og_desc, quote=True)}">
{og_tags}
<meta name="generator" content="bullshit-detector {html.escape(version)}">
<meta name="theme-color" content="#FFF200">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#{claims_anchor or 'bottom-line'}">Skip to claims</a>
<main>
<header class="hero">
  <p class="eyebrow">BS Report</p>
  <h1>{heading}</h1>
  {f'<p class="source">{inline(source_raw)}</p>' if source_raw else ""}
  {f'<p class="checked">{inline(checked_raw)}</p>' if checked_raw else ""}
  {hero_score}
  {warn_html}
</header>
{tally_html}
{filters}
<div id="claims"></div>
{"".join(section_html)}
<footer>
  {run_html}
  <p class="colophon">Generated by <a href="https://github.com/SerhiiKorniienko/bullshit-detector"
    rel="noopener noreferrer" target="_blank">bullshit-detector</a> {html.escape(version)}.
    Verdicts require sources; a report is a dated reading, not a permanent verdict.</p>
</footer>
</main>
<script>{JS}</script>
</body>
</html>
"""


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --fg:#000;--bg:#fff;--yellow:#FFF200;--cyan:#00FFFF;--magenta:#FF00FF;--grey:#F5F5F5;
  --border:4px;--pad:clamp(16px,4vw,40px);
}
html{-webkit-text-size-adjust:100%}
body{
  background:var(--grey);color:var(--fg);
  font:400 17px/1.55 'Helvetica Neue',Helvetica,Arial,system-ui,sans-serif;
  padding:var(--pad);
}
main{max-width:1180px;margin:0 auto;background:var(--bg);
  border:var(--border) solid var(--fg);box-shadow:12px 12px 0 var(--fg);padding:var(--pad)}
a{color:var(--fg);text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:2px}
a:hover{background:var(--yellow)}
code{font:600 .88em/1.4 'SF Mono',Menlo,Consolas,monospace;background:var(--grey);
  border:2px solid var(--fg);padding:1px 5px;word-break:break-word}
pre{background:var(--grey);border:var(--border) solid var(--fg);padding:16px;overflow-x:auto;margin:20px 0}
pre code{border:0;background:none;padding:0}
strong{font-weight:900}

.skip{position:absolute;left:-9999px}
.skip:focus{left:auto;position:static;display:inline-block;background:var(--yellow);
  border:3px solid var(--fg);padding:8px 14px;font-weight:900;margin-bottom:12px}

.eyebrow{display:inline-block;background:var(--fg);color:var(--yellow);font-weight:900;
  text-transform:uppercase;letter-spacing:3px;font-size:14px;padding:7px 14px;margin-bottom:20px}
.hero h1{font-weight:900;font-size:clamp(28px,5.2vw,52px);line-height:1.08;
  letter-spacing:-.02em;margin-bottom:18px;overflow-wrap:break-word}
.source{font-size:clamp(15px,2vw,18px);font-weight:700;margin-bottom:6px}
.checked{font-size:14px;text-transform:uppercase;letter-spacing:1px;font-weight:700;
  color:#444;margin-bottom:24px}
.parse-warning{margin-top:16px;border-left:8px solid var(--magenta);padding:8px 14px;
  font-size:14px;font-weight:700;background:var(--grey)}

.score{display:inline-flex;flex-direction:column;align-items:flex-start;
  border:8px solid var(--fg);box-shadow:12px 12px 0 var(--fg);padding:18px 30px;margin:6px 0 22px}
.score--none{background:var(--grey)}
.score-num{font-weight:900;font-size:clamp(56px,12vw,104px);line-height:.95;letter-spacing:-.04em}
.score-den{font-size:.42em;letter-spacing:0}
.score-band{font-weight:900;text-transform:uppercase;letter-spacing:3px;font-size:clamp(13px,2vw,18px);margin-top:6px}
.score-verdict{font-weight:700;font-size:clamp(17px,2.6vw,24px);line-height:1.35;
  border-left:10px solid var(--fg);padding-left:16px}

.tally-box{border:var(--border) solid var(--fg);background:var(--yellow);padding:16px 20px;margin:28px 0}
.tally{font-size:16px;line-height:1.5}
.tally--ambig{margin-top:8px;border-top:3px solid var(--fg);padding-top:8px}

.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 30px;
  position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0}
.chip{font:900 13px/1 'Helvetica Neue',Helvetica,Arial,sans-serif;text-transform:uppercase;
  letter-spacing:1px;background:var(--bg);color:var(--fg);border:3px solid var(--fg);
  padding:9px 12px;cursor:pointer;box-shadow:3px 3px 0 var(--fg)}
.chip:hover{transform:translate(-1px,-1px);box-shadow:4px 4px 0 var(--fg)}
.chip.is-on{background:var(--chip,var(--yellow));transform:translate(2px,2px);box-shadow:1px 1px 0 var(--fg)}
.chip .n{display:inline-block;background:var(--fg);color:var(--bg);padding:2px 6px;margin-left:5px;font-size:11px}
.chip.is-on .n{background:var(--bg);color:var(--fg)}

.section{margin:0 0 40px}
.section h2{font-weight:900;font-size:clamp(21px,3.4vw,30px);text-transform:uppercase;
  letter-spacing:-.01em;border-bottom:8px solid var(--fg);padding-bottom:8px;margin:36px 0 18px}
.section h3{font-weight:900;font-size:20px;margin:24px 0 10px}
.section p{margin:0 0 14px}
.section ul,.section ol{margin:0 0 16px;padding-left:22px}
.section li{margin-bottom:9px}
.section blockquote{border-left:10px solid var(--fg);background:var(--grey);
  padding:12px 18px;margin:0 0 16px;font-weight:700}
.callout{border-left:10px solid var(--yellow);padding-left:14px}
.section--key{border:var(--border) solid var(--fg);background:var(--yellow);
  padding:6px var(--pad) var(--pad);margin-bottom:40px;box-shadow:8px 8px 0 var(--fg)}
.section--key h2{border-bottom-color:var(--fg)}
.section--hostile{background:var(--cyan)}

.table-wrap{overflow-x:auto;border:var(--border) solid var(--fg);margin-bottom:18px}
table{border-collapse:collapse;width:100%;font-size:15px}
th{background:var(--fg);color:var(--bg);font-weight:900;text-transform:uppercase;
  letter-spacing:1px;font-size:12px;text-align:left;padding:10px;white-space:nowrap}
td{border-top:3px solid var(--fg);padding:11px 10px;vertical-align:top;overflow-wrap:anywhere}
tbody tr:nth-child(even){background:var(--grey)}
/* Fixed layout: auto layout hands the Evidence column everything and wraps the
   claim itself every three words, and the claim is the thing being judged. */
.claims table{table-layout:fixed}
.claims td:nth-child(1),.claims th:nth-child(1){width:3.25rem;text-align:center;font-weight:900}
.claims th:nth-child(2){width:25%}
.claims th:nth-child(3){width:6.5rem}
.claims th:nth-child(4){width:8.5rem}
/* The verdict is what a reader scans for, so the verdict carries the colour. */
.claim-row[data-verdict] .verdict-cell{background:var(--v,transparent);color:var(--fg);
  font-weight:900;text-transform:uppercase;font-size:.78em;letter-spacing:.5px}
/* Hiding is a screen affordance. Print shows the whole report — a filtered PDF
   would be a report that quietly dropped rows, which is the one thing this tool
   cannot ship. */
@media screen{.is-hidden{display:none!important}}

footer{border-top:8px solid var(--fg);padding-top:16px;margin-top:12px}
.run{font-style:italic;font-size:14px;color:#333;margin-bottom:8px}
.colophon{font-size:13px;color:#444;line-height:1.5}

@media (max-width:900px){
  body{padding:10px}
  main{box-shadow:6px 6px 0 var(--fg);padding:16px}
  .filters{gap:6px}
  .table-wrap{border:0;overflow-x:visible}
  table,thead,tbody,tr,td{display:block;width:100%}
  /* Off-screen, not left:-9999px — an absolutely positioned thead at a negative
     offset widens the initial containing block and gives the page a horizontal
     scrollbar on iOS. */
  thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  tr{border:var(--border) solid var(--fg);box-shadow:5px 5px 0 var(--fg);
     margin-bottom:18px;background:var(--bg)!important;padding:0}
  td{border-top:0;padding:9px 12px}
  td+td{border-top:3px solid var(--fg)}
  td:first-child{width:auto;text-align:left;background:var(--fg);color:var(--bg);font-size:13px;
    text-transform:uppercase;letter-spacing:2px}
  .claim-row td:first-child::before{content:"Claim "}
  td:not(:first-child)::before{content:attr(data-label);display:block;font-weight:900;
    font-size:10px;text-transform:uppercase;letter-spacing:2px;color:#555;margin-bottom:3px}
}

@media print{
  body{background:#fff;padding:0;font-size:11pt}
  main{border:0;box-shadow:none;padding:0;max-width:none}
  .filters,.skip{display:none}
  .is-hidden{display:revert!important}
  a{text-decoration:none}
  a[href^="http"]::after{content:" (" attr(href) ")";font-size:8pt;word-break:break-all}
  tr,.section--key,.tally-box{break-inside:avoid}
  .section h2{break-after:avoid}
}
"""

JS = """
(function(){
  var chips=[].slice.call(document.querySelectorAll('.chip[data-filter]'));
  var rows=[].slice.call(document.querySelectorAll('.claim-row'));
  var lb=document.querySelector('.chip[data-toggle="loadbearing"]');

  function apply(filter){
    var want=filter==='all'?null:filter.split(' ');
    rows.forEach(function(r){
      var v=r.getAttribute('data-verdict');
      r.classList.toggle('is-hidden', !!want && want.indexOf(v)===-1);
    });
    chips.forEach(function(c){c.classList.toggle('is-on', c.getAttribute('data-filter')===filter);});
  }
  chips.forEach(function(c){
    c.addEventListener('click',function(){apply(c.getAttribute('data-filter'));});
  });
  if(lb){
    lb.addEventListener('click',function(){
      var on=lb.classList.toggle('is-on');
      [].forEach.call(document.querySelectorAll('.section--incidental'),function(s){
        s.classList.toggle('is-hidden',on);
      });
    });
  }
})();
"""


# ---------------------------------------------------------------------------
# The compliance gate
# ---------------------------------------------------------------------------

def find_tally(explicit: str | None) -> Path | None:
    """Locate the detector's tally.py.

    Skills ship as independent directories, so `report-card` can be installed
    without `bullshit-detector` and the gate simply will not be there. That is a
    reason to warn, not a reason to fail — a missing validator must not stop
    someone viewing a report they already have.
    """
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None

    env = os.environ.get("BULLSHIT_DETECTOR_TALLY")
    if env and Path(env).expanduser().is_file():
        return Path(env).expanduser()

    here = Path(__file__).resolve()
    rel = Path("bullshit-detector") / "scripts" / "tally.py"
    candidates = [
        # Repo / plugin layout: skills/publishing/report-card/scripts/ -> skills/analysis/…
        here.parents[3] / "analysis" / rel,
        # Flat install: ~/.claude/skills/report-card/scripts/ -> ~/.claude/skills/…
        here.parents[2] / rel,
        Path.home() / ".claude" / "skills" / rel,
        Path.home() / ".agents" / "skills" / rel,
    ]
    return next((c for c in candidates if c.is_file()), None)


def gate(report: Path, tally: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(tally), str(report)],
                          capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def open_in_browser(path: Path) -> bool:
    """Best effort. A headless host or a sandbox has nothing to open, and that is
    not a rendering failure — the file is written either way."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(path)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def summary(meta: dict, src: Path, out: Path, opened: bool) -> str:
    """The handoff block. Everything in it was recounted by tally.py seconds ago,
    so the agent pastes it rather than reconstructing the numbers."""
    lines = []
    if meta["score"] is not None:
        lines.append(f"BS score {meta['score']}/10 · {meta['band']}")
        if meta["verdict"]:
            lines.append(f"  {meta['verdict']}")
    if meta["tally"]:
        lines.append(meta["tally"])
    if meta["ambiguous"]:
        lines.append(meta["ambiguous"])
    if meta["run"]:
        lines.append(meta["run"])
    if meta["missing"]:
        lines.append(f"missing header fields: {', '.join(meta['missing'])}")
    # file:// URIs, not bare paths: terminals linkify a bare URL, so both files
    # are one cmd-click away from opening. as_uri() also escapes spaces, which a
    # raw path in a reports directory under a user's name will eventually contain.
    lines += ["", f"markdown  {src.as_uri()}", f"page      {out.as_uri()}"]
    if opened:
        lines.append("          opened in your browser")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a BS report as a self-contained HTML card")
    ap.add_argument("report", help="path to the report .md")
    ap.add_argument("-o", "--out", help="output path (default: same name, .html)")
    ap.add_argument("--og-image", help="absolute URL for the link-preview image")
    ap.add_argument("--tally", help="path to tally.py (default: found automatically)")
    ap.add_argument("--no-check", action="store_true",
                    help="skip the compliance gate entirely (for non-report markdown)")
    ap.add_argument("--force", action="store_true",
                    help="render even when the report fails the gate; failures print as warnings")
    ap.add_argument("--open", action="store_true", dest="open_",
                    help="open the rendered page in the default browser (skipped when the "
                         "page already exists, so a re-render doesn't spawn a second tab)")
    ap.add_argument("--reopen", action="store_true",
                    help="open even if the page already existed — for a later session")
    ap.add_argument("--quiet", action="store_true",
                    help="print only the output path, not the summary block")
    args = ap.parse_args()

    src = Path(args.report)
    if not src.is_file():
        sys.exit(f"ERROR: no such file: {src}")

    md = src.read_text(encoding="utf-8")
    if "BS score" not in md and "## Claims" not in md and "claims" not in md.lower():
        print(f"WARNING: {src.name} does not look like a BS report; rendering anyway.",
              file=sys.stderr)

    if not args.no_check:
        tally = find_tally(args.tally)
        if tally is None:
            print("WARNING: could not locate tally.py — rendering WITHOUT the compliance check.\n"
                  "HINT: pass --tally <path>, or set BULLSHIT_DETECTOR_TALLY.", file=sys.stderr)
        else:
            code, output = gate(src, tally)
            if code == 2:
                print(output.rstrip(), file=sys.stderr)
                if not args.force:
                    print(
                        f"\nREFUSED: {src.name} does not pass tally.py.\n"
                        "Fix what it names above and re-run — a report that fails its own "
                        "arithmetic must not be rendered into a page that looks authoritative.\n"
                        "Pass --force if you know what you are doing.", file=sys.stderr)
                    sys.exit(3)
                print("WARNING: --force given; rendering a non-compliant report.", file=sys.stderr)
            elif code not in (0, 2):
                print(f"WARNING: tally.py exited {code} — rendered without a verdict on "
                      f"compliance.\n{output.rstrip()}", file=sys.stderr)

    out = Path(args.out) if args.out else src.with_suffix(".html")
    existed = out.exists()
    meta, page = build(md, args.og_image)
    out.write_text(page, encoding="utf-8")

    # Don't reopen a tab the user already has. Re-rendering is normal — the run
    # line gets finalised after a first pass — but every --open spawns another
    # window, and three consecutive real runs left the user with two. If the page
    # was already on disk, refresh it silently and say so.
    want_open = args.open_ or args.reopen
    fresh = not existed or args.reopen
    reopened = want_open and not fresh
    opened = open_in_browser(out) if (want_open and fresh) else False
    if want_open and fresh and not opened:
        print("NOTE: could not open a browser here; the file is written.", file=sys.stderr)
    if reopened:
        print(f"NOTE: {out.name} already existed — updated in place, not reopened. "
              f"Reload the tab you have, or pass --reopen.", file=sys.stderr)

    print(out if args.quiet else summary(meta, src.resolve(), out.resolve(), opened))


if __name__ == "__main__":
    main()
