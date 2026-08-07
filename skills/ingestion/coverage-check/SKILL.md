---
name: coverage-check
description: Count how many independent origins are behind news coverage of a claim, instead of counting URLs. Queries GDELT for matching articles, collapses reprints and wire copy into single origins, and flags publication bursts that indicate syndication. Use when a claim appears to be confirmed by many outlets and you need to know whether that's many sources or one source many times.
---

# coverage-check

Ten URLs are not ten sources. This turns "lots of outlets reported it" into a number you can defend.

## When to reach for it

During claim verification, when a claim looks *corroborated by volume* — a pile of search results
all saying the same thing. That pattern has two very different causes:

- Many newsrooms independently established the fact → genuinely strong evidence
- One press release, wire story, or study got reprinted 40 times → **one** source

Search results look identical in both cases. This tells them apart.

## Usage

```bash
uv run scripts/coverage.py "<query>" [--timespan 3m] [--max 250] [--sort dateasc] [--timeout 120] [--json]
```

**It is slow. This is normal.** GDELT takes ~15s for a trivial one-day query and considerably longer
for a 3-month window at 250 records. The script prints progress to stderr and how long the call took,
so you can tell "working" from "hung" — if you see the querying line, wait. Narrowing `--timespan` is
the speed lever; raise `--timeout` before assuming it's broken.

The query accepts GDELT operators: `"exact phrase"`, `(a OR b)`, `-exclude`,
`domain:example.com`, `sourcelang:english`. Quote the distinctive phrasing of the claim — a
verbatim phrase is what catches reprints.

```bash
# Is this "40 outlets confirmed it" or one wire story?
uv run scripts/coverage.py '"quantum breakthrough" AND university'

# Narrow to the week the claim surfaced
uv run scripts/coverage.py '"record quarterly revenue" domain:reuters.com' --timespan 7d
```

## Reading the output

The first line is the verdict the detector needs. The rest supports it.

- **Distinct story clusters** — articles grouped by headline similarity. This is the origin
  estimate. Outlets ≫ clusters means syndication.
- **⚠️ syndicated** on a cluster — multiple outlets published the same story inside 24h. Treat the
  whole cluster as one source.
- **wire-attributed headline** on a cluster — a headline names a wire service or press-release
  distributor (Reuters, AP, PR Newswire…). The strongest mechanical one-origin signal available
  at headline level; bodies would catch more, but GDELT returns none.
- **Duplicate URLs collapsed** — the same page counted twice behind tracking params, `www.`, or a
  trailing slash. Collapsed before anything else is counted, so every number below it is already
  deduplicated.
- **Span (hours)** — a tight burst points at a press release or embargo lift; coverage developed
  over weeks is more likely independent.

Feed the result into the report's evidence column as an origin count: *"6 results, 1 origin (all
reprints of the company's press release)"* is worth more than six links.

## Limits — read these before trusting a number

- **Rolling 3-month window only.** GDELT DOC 2.0 does not reach further back. For an older claim
  this returns nothing, and **nothing does not mean unreported**. The script says so in its output;
  don't let the agent quietly read empty as disconfirming.
- **Clustering is headline similarity**, on two measures: sequence ratio for reworded headlines and
  token overlap for the same facts in a different order. Grouping is transitive — three outlets on
  one wire story stay together even when the two extremes score below the bar individually.
  Verbatim reprints, rewritten wire copy and reordered headlines all collapse correctly.

  What it still won't catch: two newsrooms that independently reached the same finding and described
  it in genuinely different words. Those show as separate clusters, which is the safe direction to be
  wrong in — it *under*-reports syndication rather than inventing it.

  Thresholds were tuned against real GDELT output, not guessed. If you see false merges, raise
  `TITLE_MATCH`/`TOKEN_MATCH` in the script; if wire copy slips through as distinct, lower them.
- **Presence is not credibility.** A claim covered by 200 outlets in 30 distinct clusters is
  *widely reported*, not *true*. Verdicts still need the source hierarchy in the detector's
  [RUBRIC.md](../../analysis/bullshit-detector/RUBRIC.md).
- **Results cap at 250 per query.** When the cap is hit the output says so — every count becomes a
  lower bound, and the honest fix is a narrower `--timespan`, not a bigger number.
- **The free endpoint is unreliable, and this is the important one.** GDELT returns *"Please limit
  requests to one every 5 seconds"* well below that rate whenever its public API is busy —
  independent of IP, User-Agent, and query size. Measured behaviour: identical calls succeed and
  fail minutes apart. The script retries with growing backoff and then **exits 3**.

  **Exit 3 means "unmeasured", not "no coverage".** Never let a failed check weaken or strengthen a
  verdict, and never record it as though the search came back empty. If the tool can't measure, the
  report says the origin count is unknown and falls back to the eyeball tells in
  [RUBRIC.md](../../analysis/bullshit-detector/RUBRIC.md). Retry in a few minutes, or skip it.

  | Exit | Meaning |
  |---|---|
  | 0 | measurement succeeded (including a legitimate zero-result window) |
  | 1 | bad input or unreachable host |
  | 3 | GDELT throttled — no measurement, claim is unmeasured |
- **No API key, no auth, free.** Nothing to configure, nothing to rotate.

## What it does not do

It counts and groups coverage. It does not fetch article text — that's
[fetch-content](../fetch-content/SKILL.md) — and it does not judge anything. Analysis skills read
its output; they never call it to decide a verdict on their own.
