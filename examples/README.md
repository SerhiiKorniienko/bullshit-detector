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
GitHub Pages — **[read the latest one in your browser](https://serhiikorniienko.github.io/bullshit-detector/examples/0.14.0/report-clawwork-ai-salary-tweet.html)**.
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

## [0.14.0](./0.14.0/)

The composed-report release: the claims tables are rendered by `tally.py --compose` from a
`claims.jsonl` written during verification, so the table cannot disagree with the tally that
counts it — and the run footer names the instrument (`model`, and `effort`/`mode` when known).

- [report-clawwork-ai-salary-tweet.md](./0.14.0/report-clawwork-ai-salary-tweet.md) ·
  [page](./0.14.0/report-clawwork-ai-salary-tweet.html) ·
  [claims.jsonl](./0.14.0/report-clawwork-ai-salary-tweet.claims.jsonl) — a viral tweet about an
  AI that "has to earn its own salary or go bankrupt" — **4/10**

  The specs all verify against the primary sources; the deception is one omission — the "salary"
  is simulated (`quality × estimated hours × BLS wage`, no client pays anything) while only the
  token costs are real. The first example produced by the compose flow, claims file included.

## [0.13.0](./0.13.0/)

Untrusted-content fencing, quote integrity checked against the cached source, a recency axis in the
source hierarchy, and a warning tier that prints without blocking.

- [report-south-korea-ai-bubble.md](./0.13.0/report-south-korea-ai-bubble.md) ·
  [page](./0.13.0/report-south-korea-ai-bubble.html) — "South Korea's AI Bubble Just Popped",
  Andrei Jikh, 2.71M views — **4/10**

  The same video as the 0.12.1 report below, which makes the pair the clearest illustration of why
  this folder is filed by release. **60 claims extracted against 46, and 35 confirmed against 23** —
  it found more of the video to be true *and* more of it to be wrong (7 misleading and 3 false,
  against 4 and 2), so the lower score is a fuller reading rather than a softer one.

  Where it earns the release: claims 23 and 24 rate *"Samsung was up over 500%"* and *"SK Hynix was
  up over 1,000%"* 🟠 misleading, and the evidence cell shows **all three measurement bases** —
  calendar year to the June peak (+202% and +348%), trailing twelve months (+506% and +1,025%), and
  52-week trough to peak (+450% and +1,091%). The claim says *"this year"*, and only the other two
  bases reach the stated figures. A reader who disagrees with the verdict can see exactly which
  number they are disagreeing about, which is the whole point of naming the basis.

## [0.12.1](./0.12.1/)

Verdicts that don't depend on an invisible assumption: a claim whose inputs span a range carries the
range instead of quietly picking an end, and a merged row can never come out gentler than its
harshest part.

- [report-south-korea-ai-bubble.md](./0.12.1/report-south-korea-ai-bubble.md) ·
  [page](./0.12.1/report-south-korea-ai-bubble.html) — "South Korea's AI Bubble Just Popped",
  Andrei Jikh, 2.71M views — **5/10**

  The most thoroughly verified report here: **43 of 46 claims individually searched** (93%, against
  54 searches), with one row left `⚪ not checked` and nothing dropped as ambiguous. It is also the
  clearest example of the tool splitting a video in half rather than scoring it whole — Korea's
  crash, the margin-call mechanics and the record US margin-debt figure all check out, while the
  claims bridging the two markets do not. Three findings worth the click: the "OpenAI and Anthropic
  are 70–80% of AI compute" figure against Epoch AI's measured 20–30%; a "one in every 30 people in
  the country" ratio that only works against the working-age population; and a specific, named
  Coca-Cola/Cisco anecdote with no footprint anywhere, next to exhaustively documented coverage of
  the same event.

  One caveat, since this folder is where the rules are supposed to be visible: claim 16 merges
  OpenAI and Anthropic into a single 🟠 row when the Anthropic half is contradicted outright. Under
  the rule this very release shipped, that row should be ❌. It is left as written — a report is a
  dated reading, and editing one to fix a flaw found later is how a fact-checking artifact stops
  being evidence.

## 0.9.0 – 0.12.0

No examples. Five releases of bookkeeping and rule work — run records, unreachable-source logging,
late splits, range-carrying — shipped without a published report between them, which is a gap in
this folder rather than a gap in the releases.

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
