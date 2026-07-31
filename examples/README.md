# Published reports

Reports the tool wrote about other people's content, filed by the release that produced them.

**A report is a dated reading, not a permanent verdict.** The rubric, the source hierarchy and the
verdict rules change between releases, and web search does not return the same evidence twice — so
the same content checked a month apart can land differently. The folder says which rules were in
force; the header inside says when it ran.

That matters more here than it would elsewhere: the same video checked four times in one day
produced 18, 22, 20 and 28 claims. Comparing a report to one from another release is comparing two
instruments, not two readings.

## What's in a folder

Every report ships as **markdown** — that is the artifact `tally.py` validates and the one to diff
against a later run. From 0.8.0 a **`.html`** sits beside it: the same report rendered as a
self-contained page, produced by the [`report-card`](../skills/publishing/report-card/SKILL.md)
skill. GitHub shows `.html` as source rather than rendering it, so the pages are also served from
GitHub Pages — **[read the latest one in your browser](https://serhiikorniienko.github.io/bullshit-detector/examples/0.8.0/report-needle-at-the-speed-of-light.html)**.
The file itself is self-contained: no network requests in it, so a downloaded copy keeps working
offline forever.

Older reports are deliberately **not** back-rendered. The renderer arrived in 0.8.0; an HTML page
built from a 0.6.0 report would be a 0.8.0 artifact wearing a 0.6.0 stamp, and it would silently
change every time the renderer changes while the markdown beside it stayed frozen. The markdown is
the reading; the page is a view of it, and only where the two shipped together.

From 0.7.0 the **`.run.json`** run record is committed too — self-reported, never part of the
report, and the only data `scripts/runstats.py` has to work with on a fresh clone.

## Two videos, checked repeatedly

Two of these are the same content read by successive releases, which is the clearest demonstration
of the warning above:

- **"The Claude Situation Is a Total Sh\*tshow"** — [0.5.0](./0.5.0/report-claude-situation-shitshow.md)
  → [0.6.1](./0.6.1/report-claude-situation-shitshow.md) → [0.7.0](./0.7.0/report-claude-situation-shitshow.md).
  Same score all three times, 5/10. What moved is everything under it: 20 claims to 24 to 19, and
  **one clickable source in the first, forty-one in the second**.
- **"How to Build a $1M YouTube Channel in 1 Hour a Day"** — [0.5.0](./0.5.0/report-1m-youtube-channel.md)
  → [0.6.0](./0.6.0/report-1m-youtube-channel.md). 7/10 to 6/10, and the later run **drops four
  claims as ambiguous** — the first release that could.

## [0.8.0](./0.8.0/)

Presentation: reports render to a self-contained HTML page, and the renderer refuses a report that
fails `tally.py`.

- [report-needle-at-the-speed-of-light.md](./0.8.0/report-needle-at-the-speed-of-light.md) ·
  [page](./0.8.0/report-needle-at-the-speed-of-light.html) — "What If a Needle Hit The Earth At The
  Speed Of Light?", What If (Underknown), 906K views — **5/10**

  The largest report here: 42 claims, all 42 individually searched, 69 linked sources. Relativistic
  arithmetic is worked in the evidence cells (γ−1 = 21.37 at 0.999c, so 1 Mt needs a 2.2 g needle),
  which is what lets it say the destruction figures are inflated rather than just asserting it.

## [0.7.0](./0.7.0/)

The release that made runs report what they cost — a one-line run footer and a `.run.json` record.

- [report-how-to-get-so-rich-as-a-dev.md](./0.7.0/report-how-to-get-so-rich-as-a-dev.md) — "How to
  Get So Rich as a Dev It Feels Illegal", Bgo, 18K views — **7/10**

  Course-funnel content, and the case the rubric cares about: every number the video offers as proof
  is private by construction. The report scores the checkable perimeter and says so in a load-bearing
  warning rather than pretending the core was audited. Auditing this report is what produced issues
  #23, #24 and #25.
- [report-claude-situation-shitshow.md](./0.7.0/report-claude-situation-shitshow.md) — "The Claude
  Situation Is a Total Sh\*tshow", Meerkat Explains, 84K views — **5/10**

## [0.6.1](./0.6.1/)

Evidence you can click: every searched verdict must link something.

- [report-imf-weo-update.md](./0.6.1/report-imf-weo-update.md) — "World Economic Outlook Update,
  July 2026", the IMF's own channel, 57K views — **1/10**

  The tool finding nothing wrong. An official body accurately reproducing its own primary document
  scores 1, and the report says so plainly. A detector that never returns a low score is not
  detecting anything.
- [report-claude-situation-shitshow.md](./0.6.1/report-claude-situation-shitshow.md) — "The Claude
  Situation Is a Total Sh\*tshow", Meerkat Explains, 84K views — **5/10**

## [0.6.0](./0.6.0/)

Pin the claim down, then check it: the disambiguation gate, and a count of what got dropped.

- [report-1m-youtube-channel.md](./0.6.0/report-1m-youtube-channel.md) — "How to Build a $1M YouTube
  Channel in 1 Hour a Day", Sunny Lenarduzzi, 141K views — **6/10**

  Four claims dropped before verification because the video never fixes what they refer to. The
  0.5.0 reading of the same video kept them.

## 0.5.1

No example. 0.5.1 shipped extensionless-PDF handling and a source-of-sources — neither of which any
report from that day demonstrates, and a filler example is worse than an honest gap.

## [0.5.0](./0.5.0/)

The release that added the five-tier source hierarchy and syndication collapse.

- [report-1m-youtube-channel.md](./0.5.0/report-1m-youtube-channel.md) — "How to Build a $1M YouTube
  Channel in 1 Hour a Day", Sunny Lenarduzzi, 137K views — **7/10**
- [report-claude-situation-shitshow.md](./0.5.0/report-claude-situation-shitshow.md) — "The Claude
  Situation Is a Total Sh\*tshow", Meerkat Explains, 45K views — **5/10**

## [0.4.x](./0.4.x/)

Before reports carried a version stamp, so the exact release is only recoverable for one of them.
They also predate the rule that evidence must be clickable, and cite sources they do not link.

- [report-14-ways-to-make-money-with-ai.md](./0.4.x/report-14-ways-to-make-money-with-ai.md) — "The
  Only 14 Ways to Make Money with AI in 2026", Dan Martell, 1.16M views — **5/10**
- [report-second-sun-binary-star.md](./0.4.x/report-second-sun-binary-star.md) — "Is our Sun part of
  a binary star system?", @tcpwithjosh, 552K views — **9/10**
- [report-own-readme.md](./0.4.x/report-own-readme.md) — this repository's own README, checked at
  v0.4.1 after someone on Hacker News asked for the obvious test — **3/10**

## Adding one

New reports go in a folder named for the release that produced them, created on first use. The
version in the report header and the folder name must agree — if they don't, one of them is lying
about which rules were applied.

Reports must pass `uv run skills/analysis/bullshit-detector/scripts/tally.py <report>` before they
are published. Reports from earlier releases are not re-validated against later rules: `tally.py`
gates each check on the version it shipped in, so an old report is judged by the rules it was
written under.

Then render the page beside it — the renderer runs the gate again and refuses if it fails, so this
is also the check:

```bash
uv run skills/publishing/report-card/scripts/render_report.py examples/<version>/<report>.md
```

If a `.run.json` goes in too, rewrite its `report` field to the repo-relative path. The record is
written with an absolute path on whoever ran it, which leaks a home directory and is wrong for
everyone who clones.
