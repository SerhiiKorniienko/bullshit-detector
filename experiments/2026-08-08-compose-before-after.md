# Does `--compose` make a run faster? No. Does it make it better? Measurably, maybe.

**Setup.** Six blind runs of the same video (`hy90LdpEUvQ`, the `kospi-ai-bubble` eval case),
same harness (`eval/run-case.sh`, sonnet, `effort: xhigh`, transcript pre-fetched, installed
skill paths handed over, runner never told it is timed), one variable: the first three ran the
0.13.1 hand-written-table flow, the last three ran the 0.14.0 `--compose` flow (claims stream
to `.claims.jsonl` during verification, `tally.py --compose` renders the tables, model writes
prose only). Wall and phase data measured externally with `scripts/runprofile.py`; quality
scored against the case's labelled claims with `eval/score.py` (labels are drafts pending
owner review — treat absolute values with that caveat; the *comparison* between arms uses the
same labels both sides).

## Wall clock and volume — the hypothesis fails

| run | arm | wall | thinking | searches | output tokens |
|---|---|---|---|---|---|
| 1 | baseline | 21.8m | 944s | 49 | 104K |
| 2 | baseline | 18.4m | 799s | 47 | 106K |
| 3 | baseline | 26.6m | 1244s | 44 | 137K |
| 4 | compose | 25.2m | 1101s | 44 | 132K |
| 5 | compose | 28.1m | 1227s | 53 | 148K |
| 6 | compose | 21.6m | 885s | 54 | 105K |

Median wall **21.8m → 25.2m**, ranges fully overlapping. Median output tokens **106K → 132K**.
The emission the table no longer costs comes back as the claims file — each JSONL line carries
the same evidence prose the table row would have — plus the shell, plus more tally invocations
(3 → 7–10 per run). **The mechanism was named before it was measured, again** (fourth
instance; see #45's retraction and the #47 parallelism post-mortem). The table was never the
expensive part of compose — the *thinking about the report* was, and that is unchanged.

Phase-split caveat: `runprofile.py`'s classifier predates the compose flow (a `*.shell.md`
write matches its report anchor), so per-phase attribution for the compose arm is unreliable.
Wall, thinking, searches and tokens are mechanical and stand.

## Quality — every gap favours compose, none is conclusive at n=3

| metric (median) | baseline | compose |
|---|---|---|
| extraction recall | 0.783 | 0.733 |
| exact verdict agreement | 0.628 | 0.667 |
| tolerated agreement | 0.791 | 0.792 |
| QWK | 0.523 | 0.524 |
| **known-true confirm rate** | **0.667** (0.633–0.767) | **0.800** (0.700–0.833) |
| known-false catch | 4/4, 4/4, 3/4 | 4/4 ×3 |

Known-true is the one near-separation: the compose arm's worst run beat two of three baseline
runs. A claim written down the moment its verdict resolves may simply survive to the table
more reliably than one recalled at compose time — but that is a story fitted to six runs, not
a finding. The laundered K10+K11 merge appeared in 5 of 6 runs in both arms; the eval catches
it every time, the skill does not yet prevent it (that is #16's next argument).

## What compose actually buys, measured or structural

- **The table-vs-tally divergence class is dead by construction** — the tables are counted by
  the same parse that gates them. That class produced a real published-page disagreement.
- **A truncated run now costs one claim, not the run** (JSONL durability).
- **Gate rework stays solved**: run 5 passed 9 of 9 tally invocations clean.
- Teething, both fixable in wording: two compose runs typed a future `finished` timestamp into
  the run record (the #38 anchor caught both), and one quoted a span not in the source
  (quote-integrity caught it).

## Verdict

Keep `--compose` — as a correctness feature. Drop every performance claim from its story. The
run's clock is deliberation (thinking 72% at xhigh, three 130–180s blocks in every run
regardless of arm), and the only measured lever on that remains the effort knob (−35% wall,
3× score spread — documented option, not the default). Wall-time work should stop targeting
emission; there is nothing left there.
