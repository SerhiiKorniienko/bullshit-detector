# The run record — `bullshit-detector/run@1`

Written beside every report: same path, `.md` swapped for `.run.json`.

**Read this file only when you are writing the record.** It is diagnostic — nothing in the report
depends on it, and if you cannot write it, skip it silently and say nothing. It is separated from
`SKILL.md` for exactly that reason: a run should not pay to read the schema of an optional artifact
before it has checked a single claim.

```json
{"schema": "bullshit-detector/run@1", "version": "<same stamp the report carries>",
 "source": "<url or file>", "report": "<report path>",
 "started": "<ISO time from step 1>", "finished": "<ISO time now>", "wall_seconds": 722,
 "claims": {"extracted": 28, "checked": 23, "dropped_ambiguous": 2},
 "source_words": 4445, "fetches": 1, "coverage_checks": 0,
 "queries": [{"claim": 3, "pass": "first", "q": "the query, verbatim"},
             {"claim": 3, "pass": "follow-up", "q": "the next angle, verbatim"}],
 "unreachable": [{"claim": 7, "url": "https://example.com/study",
                  "reason": "paywall"}]}
```

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
and a `reason` from: `paywall`, `blocked` (bot wall, 403, crawler block), `dead` (404, domain gone),
`timeout`, `login`. Omit the field entirely when nothing was blocked.

RUBRIC's unreachable ≠ unverifiable rule fires per row and then the information dies: nothing
aggregates it, so a reader cannot see that six claims dead-ended at the same paywalled outlet, and
nobody can tell whether it is getting worse over time. This field is the cheapest possible fix — the
agent already knows which fetches failed at the moment they fail.

## What `tally.py` cross-checks

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
