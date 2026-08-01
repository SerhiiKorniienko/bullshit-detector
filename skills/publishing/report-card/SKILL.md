---
name: report-card
description: Render a finished BS report as a self-contained HTML page — score hero, filterable claims, readable on a phone, prints to a clean PDF. Use when the user wants to open, share, print, or show a report to someone who is not going to read a markdown table, or asks for "the HTML version", "something I can send", "a shareable page", or "make this readable".
---

# report-card

Turn `bs-report-<slug>-<date>.md` into one HTML file anybody can open.

The markdown is the artifact and stays the artifact — it is what `tally.py` checks, what gets
diffed against a later run, and what gets committed. This skill adds a **reader-facing** view of
that same file. It renders; it never edits, recounts, or adds. Every number on the page is copied
from the markdown verbatim.

## Why this exists

A BS report is a five-column claims table. On a laptop that is fine. On a phone — which is where a
shared link is actually opened — the Evidence column is unreadable, and the reader's first
question ("what's wrong with it?") means scrolling twenty rows to find the two that matter.

## Usage

```bash
uv run <this-skill-dir>/scripts/render_report.py ~/.bullshit-detector/reports/<YYYY>/bs-report-<slug>-<date>.md
```

Writes `bs-report-<slug>-<date>.html` beside the markdown. `-o <path>` puts it elsewhere. No install
step, no dependencies — the script is stdlib-only, runs under plain `python3` as well as `uv run`,
and the page it produces makes no network requests. That combination is what lets it work in a
code-execution sandbox, where the HTML is the only thing the user can take away.

- `--open` shows the page in the default browser. Where there is no browser — a sandbox, a headless
  host — it says so and the file is still written. **It is skipped when the page already exists**,
  because re-rendering is normal (the run line gets finalised after a first pass) and every open
  spawns another tab — three consecutive real runs left the user with two. The file updates in
  place; reload the tab you have.
- `--reopen` opens even when the page existed — for picking a report back up in a later session. Never treat that as a failure.
- `--quiet` prints only the output path, for scripting.

## The handoff block

By default the script prints the block that ends a detector run:

```
BS score 4/10 · Mostly fine
  the macro data is real and mostly checks out; the narrative glue is crypto-Twitter.
Tally: 35 claims extracted, 34 individually source-checked — 22 confirmed, 5 plausible,
  5 misleading, 2 false. 1 not checked.
run: 16m30s, searches 35, tools 65, coverage 1, per claim 29s

markdown  file:///Users/…/bs-report-japans-money-is-collapsing-2026-07-31.md
page      file:///Users/…/bs-report-japans-money-is-collapsing-2026-07-31.html
          opened in your browser
```

**Paste it; don't rebuild it.** Every figure came out of the report that `tally.py` had just
recounted. A summary retyped from memory of what you wrote is wrong in the direction that flatters
the run — the same failure mode as the tally and the search count, one level up.

The paths are `file://` URLs on purpose: terminals linkify a bare URL, so both files are one
cmd-click from opening. Don't shorten them to `~/…` or hide them behind link text.

## The compliance gate

Before rendering, the script runs the report through the detector's `tally.py` and **refuses to
render a report that fails it**:

```
REFUSED: bs-report-our-solar-system-2026-07-31.md does not pass tally.py.
  ✗ run line: 25 claims individually source-checked from 21 searches — every claim
    carrying a verdict needs its own search, so this reports more verification than
    was performed
```

Exit 3. This is the point of the gate: a page this presentable, built from a report that fails its
own arithmetic, launders a broken report into something that looks authoritative. Fix what the gate
names and re-run.

- `--force` renders anyway and prints the failures as warnings.
- `--no-check` skips the gate — for markdown that isn't a BS report.
- `--tally <path>` or `$BULLSHIT_DETECTOR_TALLY` if it can't be found automatically.

If `tally.py` isn't installed at all — this skill can be installed without the detector — the
script warns and renders. A missing validator is a reason to warn, not a reason to stop someone
viewing a report they already have.

`--og-image <absolute-url>` adds a link-preview image. Only useful once the page is hosted
somewhere; skip it for local files.

Then tell the user the path and that it opens in any browser. On macOS `open <path>` does it.

## What the page adds over the markdown

- **Score hero** — the number at the size it deserves, coloured by the RUBRIC band (Solid /
  Mostly fine / Hype-heavy / Mostly bullshit / Fabricated), with the one-line verdict beside it.
- **Verdict filter chips** — `Problems` shows only ❌ and 🟠. `Load-bearing only` hides the
  incidental table. This is the whole reason a non-technical reader gets through the report.
- **Claims as cards under 900px**, as a table above it. Same rows, same order, same text.
- **Print stylesheet** — Cmd-P gives a clean PDF with the URLs printed after each link.
  Filters are deliberately ignored when printing: a filtered PDF is a report that quietly dropped
  rows, which is the one artifact this tool must never produce.
- **Link-preview tags** — a pasted link shows `<title> — N/10` and the verdict line instead of a
  bare URL.

## Rules

- **Render, don't re-report.** If a number looks wrong, the markdown is wrong — fix it there and
  re-render. Never correct it in the HTML.
- **The markdown is still the source of truth.** Say so when handing over the file; the HTML is a
  view, and only the markdown is what `tally.py` validated.
- **Don't reach for `--force` to make a refusal go away.** The gate is naming a real defect in the
  report. Rendering past it produces a page that looks more trustworthy than the thing behind it,
  which is the failure this whole tool exists to catch.
- **Don't publish anything without being asked.** People point this tool at unpublished drafts,
  internal docs and things they were sent in confidence. Writing a local file is not publishing;
  putting it on the internet is a separate decision that belongs to the user, per report.
- The renderer is deliberately lenient — a report missing its score or version stamp still renders,
  with a note on the page saying which fields were missing. That is a viewer's job. `tally.py` is
  the strict one, and the two must not swap roles.

## Known limits

- The claims table must keep its `| # | Claim | Type | Verdict | Evidence |` shape — the `#` column
  is how the renderer tells a claims table from any other table, and the verdict glyph is read from
  its own cell, never from anywhere else in the row.
- Reports in any language render fine (system fonts, no bundled webfont).
- Images are not generated here. The social carousel lives in
  [share](../share/SKILL.md).
