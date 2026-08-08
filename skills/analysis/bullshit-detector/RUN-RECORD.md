# The run record — `bullshit-detector/run@1`

Written beside every report: same path, `.md` swapped for `.run.json`.

**Read this file only when you are writing the record.** It is separated from `SKILL.md` so a run
does not pay to read this schema before it has checked a single claim.

**The report's run line is generated from this file.** `tally.py --fix` reads the record and writes
the footer — the wall clock from `started` and `finished`, `searches` from the query log, `coverage`
from `coverage_checks`, `tools` copied, `per claim` computed against `M` from the table.

So the record is no longer purely diagnostic. Be precise about what that does and does not mean:
**the gate does not require this file.** A report with no record beside it, carrying a hand-typed
and internally consistent footer, still passes — `run_record_problems` returns immediately when
there is no record to compare against. Writing the record is the *instructed* path because it is the
one that cannot go quietly wrong, not because anything forces it. Nothing here should ever be
restated in the report by hand: that is the two-artifacts-one-quantity failure this project exists
to catch elsewhere.

A record written before `tools` existed simply does not get a generated footer — `--fix` says which
field is missing and leaves the line alone. Nothing retroactively fails.

```json
{"schema": "bullshit-detector/run@1", "version": "<same stamp the report carries>",
 "source": "<url or file>", "report": "<report path>",
 "started": "<ISO time from step 1>", "finished": "<ISO time now>", "wall_seconds": 722,
 "claims": {"extracted": 28, "checked": 23, "dropped_ambiguous": 2},
 "source_words": 4445, "fetches": 1, "coverage_checks": 0, "tools": 30,
 "queries": [{"claim": 3, "pass": "first", "q": "the query, verbatim"},
             {"claim": 3, "pass": "follow-up", "q": "the next angle, verbatim"}],
 "unreachable": [{"claim": 7, "url": "https://example.com/study",
                  "reason": "paywall"}]}
```

## Four fields you do not write

`tally.py --fix` fills these in from the report and the timestamps, and corrects them if they are
already there and wrong. Leave them out, or leave them approximate — they will be replaced:

| field | derived from |
|---|---|
| `claims.extracted` | the claim rows in the table |
| `claims.checked` | the same recount that produces `M` for the tally line |
| `claims.dropped_ambiguous` | the `J` in the report's Ambiguous line |
| `wall_seconds` | `finished` − `started` |

This is the same rule as the tally line and the footer, applied one file further: **a number that
can be computed is never typed.** A real run reported 22 claims checked against a table of 20 — a
typo in a figure the script had already counted correctly two lines earlier.

## Three fields that name the instrument

The instrument is the release *and* what ran it: the same rules at a different reasoning effort
measurably produce a different score spread (same mean, three times the variance at `high` vs
`xhigh`), and main-session and subagent harnesses have measured 11 vs 18 minutes on identical
work. A reading that doesn't say which instrument produced it cannot be compared with anything.

| field | what to write |
|---|---|
| `model` | the model id as your harness states it, e.g. `claude-sonnet-5` |
| `effort` | the reasoning effort your harness declared, e.g. `xhigh` |
| `harness` | what is running you, e.g. `claude-code`, `codex`, `opencode` |

All three are optional strings with one rule: **write only what your harness actually told you,
and omit what you don't know.** Omission means unknown; a guessed label is worse than none,
exactly as with the version stamp. `tally.py --fix` copies `model` and `effort` into the run
footer so a fast reading can never pass as a standard one, and warns — never blocks — when they
are absent.

One more field belongs to the same idea: **`mode`** — write `"mode": "quick"` when the run used
quick mode (SKILL.md names the four budgets it cuts), and omit the field entirely on a full run.
Unlike `model` and `effort` this one is *not* optional-when-known: the gate rejects a quick
record whose report carries no **Mode: quick** disclosure line, and a disclosure line whose
record does not say quick. `--fix` prints it into the footer alongside model and effort.

It happens under `--fix` only. A plain `tally.py <report>` never writes to the record, which is what
keeps `render_report.py` — which runs the gate on every render — from mutating anything.

Everything else stays yours, because nothing else can derive it: the timestamps, the query log,
`tools`, `fetches`, `coverage_checks`, `source_words`, `unreachable`.

**`tools`** — every tool call the run made, the one figure in the footer nothing can derive for you.
It is not exact by construction and is not treated as though it were: counting it precisely would
require the very calls that change the count. Give the honest total you can see. Its only job is the
reconciliation a reader can do at a glance — a search is a tool call, so searches can never exceed
tools.

## Fields that are easy to get wrong

**`source_words`** — the word count of the normalized text saved in step 1; `fetch-content` prints
it in the frontmatter. It exists so extraction coverage stops being invisible: claims per thousand
words is the only cheap signal for whether a run read the whole thing or skimmed it, and two runs of
one video have already differed by twelve claims with nothing in either artifact to show it.
`scripts/runstats.py` reports it across releases. It is a measurement, not a target — dense content
genuinely yields more claims per word than a rambling one.

**`queries`** holds **search queries only** — one entry per search issued, including the ones that
return nothing. Fetching a page you found is not a search; it belongs in `fetches`. The two got
mixed in a real run and the record ended up claiming eight more searches than the report did.

Log each query **as you issue it**. A list rebuilt from memory at the end is wrong in the direction
that flatters the run — the same failure as the tally and the search count, one level up.

**`unreachable`** — one entry per URL you could not reach, with the claim it would have supported
and a `reason` from the closed set below. Omit the field entirely when nothing was blocked.
`tally.py` rejects a reason outside the set: free text cannot be counted across runs, and counting
causes is the only thing this field is for.

| reason | when |
|---|---|
| `paywall` | a subscription wall stands between you and the text |
| `blocked` | a bot wall, 403, or crawler block — something refused you |
| `dead` | 404, domain gone, link rotted |
| `timeout` | the request never came back |
| `login` | an account is required; never auto-solve one |
| `empty` | **the fetch succeeded and there was nothing behind it** |

`empty` is the case the original five missed. A JS-only shell, a video page with no transcript, a
PDF that extracts to zero characters — the request returned 200 and yielded no readable content.
That is not `blocked`, because nothing refused you, and not `dead`, because the URL resolves.
Logging it as either loses the one thing a later run needs to know: whether a different fetcher
would have got the text.

RUBRIC's unreachable ≠ unverifiable rule fires per row and then the information dies: nothing
aggregates it, so a reader cannot see that six claims dead-ended at the same paywalled outlet, and
nobody can tell whether it is getting worse over time. This field is the cheapest possible fix — the
agent already knows which fetches failed at the moment they fail.

## What `tally.py` cross-checks

- **`wall_seconds` must equal `finished` − `started`**, exactly — and since `--fix` now writes it
  from them, the way to get this wrong is to fabricate the timestamps themselves. That is the point:
  every other run-line check is internal (per-claim equals wall over `M`, searches never exceed
  tools) and all of them are satisfied by an invented duration used consistently. One real run
  drafted a plausible "27m40s" before it had finished and passed cleanly on the first try. The
  timestamps are the only anchor outside the report, `finished` must not be in the future, and a
  `finished` that precedes `started` is reported rather than quietly normalised.
- **The counts in the record and the run line describe the same events and must agree.** The script
  compares them whenever both exist.
- **A record listing unreachable sources against a report that never mentions them** is rejected —
  the same failure as a run line disagreeing with its record. SKILL.md step 7 has the one-line
  report disclosure this pairs with.

## Why it exists at all

So runs can be compared across releases — `scripts/runstats.py` reads these — and so the follow-up
searches in step 4 can be audited afterwards for whether they genuinely changed angle or merely
reworded the same query.

None of that is visible to a reader of the report, and none of it should be. A reader wants to know
whether the content is true, not what it cost to find out.
