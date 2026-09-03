# Results: the detector's own score, first reading

**Date:** 2026-09-03. **Rules:** the skill at commit `e585a78` (main after #54), which ships as
0.14.1; every run record stamps `0.14.0` because the manifest is bumped at release and no
rule that can move a verdict changed between the two. **Harness:** `eval/run-case.sh` in
claims-only mode, headless `claude -p`, model `claude-sonnet-5`, reasoning effort `xhigh`,
transcripts pre-fetched, skill paths handed over, runner never told it is scored or timed.
**Corpus:** the ten cases in `eval/cases/`, 480 curated claims. **Labels:** drafts, agent-
curated from primary sources, not yet reviewed by the owner (`labeled_by` says so in every
case). **Runs:** one per case, three each on `kospi-ai-bubble` and `claude-situation` for
stability, fourteen in all; wall clock 9 to 23 minutes per case, median 13.6. Claims files, run records and scorer output are filed under
`eval/runs/0.14.1/`, so the number below can be re-scored after label review without a
single re-run:

```
uv run eval/score.py eval/cases/<id> eval/runs/0.14.1/<id>-1/bs-report-<id>.md
```

## The number

Pooled over one run per case, 480 curated claims:

| metric | value | what it means |
|---|---|---|
| extraction recall | **0.704** (338 of 480) | share of curated claims a run found, whether as its own row or merged into one |
| known-true confirm rate | **0.694** (136 of 196) | share of claims labelled `confirmed` that the run rated inside their tolerance band; the release-gate number, threshold 0.95 |
| known-false catch rate | **0.692** (9 of 13) | share of claims labelled `false` that the run rated misleading or worse |
| tolerated verdict agreement | **0.835** (of 249 scored) | verdict inside the label's defensibility band |
| exact verdict agreement | 0.703 | verdict equals the label |
| laundered merges | 3, in 3 cases | a true and a false claim merged into one row rated gentler than its harshest part |

**The gate fails on every case that has enough known-true claims to test it.** The only
PASS is `rich-as-a-dev`, which has two. Nothing came within 0.1 of 0.95.

Two readings of the pooled confusion table are worth more than the rates:

- **Of 155 known-true claims the run reached, it rated 2 `false` and 9 `misleading`.** A
  false accusation rate of 7 percent on true claims is the number the "never says false"
  worry was about, and it is not zero.
- **Of 60 known-true claims the run failed to confirm, 41 were never extracted at all**, not
  mis-graded. Extraction granularity, not judgement, is the larger cause on this corpus.

## Per case, one run each

| case | rows / curated | recall | load-bearing | verdicts n | tolerated | QWK | known-true | known-false | merges |
|---|---|---|---|---|---|---|---|---|---|
| kospi-ai-bubble | 37 / 60 | 0.733 | 0.750 | 42 | 0.786 | 0.53 | 0.733 (30) | 0.50 (4) | 0 |
| claude-situation | 25 / 28 | 0.821 | 0.909 | 22 | 0.864 | 0.69 | 0.769 (13) | 1.00 (2) | 0 |
| our-solar-system | 16 / 38 | 0.632 | 0.333 | 24 | 0.917 | 0.78 | 0.600 (30) | 1.00 (1) | 0 |
| fed-inflation-jobs | 47 / 66 | 0.742 | 0.963 | 49 | 0.857 | 0.70 | 0.714 (42) | 1.00 (3) | 1 |
| clawwork-ai-salary-tweet | 10 / 17 | 0.765 | 0.750 | 13 | 0.846 | n/a | 0.750 (12) | 0.00 (1) | 0 |
| bitcoin-storage | 20 / 36 | 0.694 | 0.867 | 25 | 0.960 | 0.21 | 0.826 (23) | n/a (0) | 1 |
| needle-light-speed | 28 / 59 | 0.695 | 0.643 | 37 | 0.784 | 0.43 | 0.593 (27) | n/a (0) | 1 |
| rich-as-a-dev | 11 / 42 | 0.333 | 0.364 | 14 | 0.786 | 0.50 | 1.000 (2) | n/a (0) | 0 |
| japan-money-collapsing | 43 / 74 | 0.770 | 0.865 | 19 | 0.737 | 0.46 | 0.615 (13) | 1.00 (1) | 0 |
| britain-poor-country | 58 / 60 | 0.800 | 0.793 | 4 | 0.750 | n/a | 0.500 (4) | 0.00 (1) | 0 |

Known-true and known-false columns carry the claim count in brackets; a rate over one or
two claims is a coin, not a measurement. QWK is over the four-step truth axis and is
undefined or meaningless below about ten pairs.

**Read britain and japan as extraction cases only.** Their labellers were cut off by a
session limit and 53 of 60 and 52 of 74 rows are `null` with the settling source named in
each basis. Their verdict columns rest on four and nineteen rows and will change when the
owner labels them.

## Stability, three runs on one case

| case | claims unanimous across 3 runs | mean distinct verdicts per claim |
|---|---|---|
| kospi-ai-bubble | 31 of 60 (0.52) | 1.62 |
| claude-situation | 13 of 28 (0.46) | 1.61 |

Same content, same rules, same model, same day: half the claims got a different verdict
(or went unextracted) in at least one of three runs. On `claude-situation` the known-true
rate read 0.769, 0.538 and 0.538 across the three. That spread is the noise floor, and it
is wider than any effect a single-run comparison could claim. This is the first time it has
been measured rather than argued.

## What this reading is and is not

- **Extraction recall and known-true confirm rate are the readable numbers.** Both are
  mostly about what the run chose to list and how it graded a claim it did list.
- **Verdict agreement carries retrieval noise.** Frozen evidence packs are not built, so the
  same claim gets a different evidence base on every run and part of the disagreement is
  search luck, not judgement. Only large effects are readable in the agreement and QWK
  columns until that lands.
- **The labels are drafts.** Curated blind from primary sources by agents that were not
  allowed to read prior reports, with every basis naming its source, but not yet read by a
  person. A harness whose labels the tool's own author reviews narrows the "author-picked
  content" limitation; it does not remove it.
- **Granularity is the confound.** `our-solar-system` lists 38 curated claims and the run
  wrote 16 rows, then graded those 16 well (tolerated 0.92). `rich-as-a-dev` lists 42 and
  the run wrote 11, leaving most opinion and anecdote rows out of its table entirely. A
  curator who slices finer than the run pushes recall down and the merge count up without
  any verdict being wrong. Where that is curation and where it is the run's loss is the
  review queue's question, and the scorer prints it for a person to answer.
- **One arm.** All fourteen runs are claims-only, sonnet, xhigh. `experiments/2026-09-02-
  claims-only-delta.md` measured that arm against full mode on one case and found the
  same quality band; a different model or effort is a different instrument and gets its
  own table.

## What moves next

1. Owner review of the labels, britain and japan first. Re-score with the command above.
2. Frozen evidence packs, so a rule change is the only variable between two readings.
3. The merge rule (#16). Three laundered merges in ten cases, and five of six on
   `kospi-ai-bubble` across two experiments, all on pairs the corpus was built to catch.
4. Extraction of opinion and anecdote rows: the skill says list them, two runs did not.
