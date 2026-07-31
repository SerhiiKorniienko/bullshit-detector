# Published reports

Reports the tool wrote about other people's content, filed by the release that produced them.

**A report is a dated reading, not a permanent verdict.** The rubric, the source hierarchy and the
verdict rules change between releases, and web search does not return the same evidence twice — so
the same content checked a month apart can land differently. The folder says which rules were in
force; the header inside says when it ran.

That matters more here than it would elsewhere: the same video checked four times in one day
produced 18, 22, 20 and 28 claims. Comparing a report to one from another release is comparing two
instruments, not two readings.

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
