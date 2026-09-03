# Eval harness

The answer to "how often is it wrong" — the gap named in the Show HN post, tracked as
[#3](https://github.com/SerhiiKorniienko/bullshit-detector/issues/3), and the reason every
accuracy question about this tool has so far ended in "unfalsifiable". The design here
implements the fixture-corpus spec recorded on that issue.

## Why this exists

Run-to-run variance exceeds every effect worth measuring. The same video, same rules, has
produced 18/22/20/28 extracted claims across four runs; a prompt A/B could not be read
because search noise swamped it; two confident regression diagnoses dissolved when a third
data point arrived. Without labelled ground truth the instrument cannot tell a regression
from noise — so neither can anyone using it.

## The corpus

One directory per case under `cases/`:

```
cases/<id>/
  transcript.md   — the source, fetched once, committed verbatim. Extraction is
                    reproducible without a network fetch or a residential IP.
  case.json       — metadata + the hand-curated claim list with labels.
```

`case.json` is `bullshit-detector/eval-case@1`:

| field | meaning |
|---|---|
| `quote` | verbatim span from `transcript.md` — the stable identifier. Claim *numbers* are not stable across runs (measured: the same content sliced into 18–28 rows), so cases key on the assertion, never the row. |
| `claim` | the decontextualized standalone assertion |
| `type` | factual / prediction / opinion / anecdote |
| `load_bearing` | the content's thesis rests on it |
| `label` | expected verdict, or `null` when ground truth could not be established (an honest null beats a guessed label) |
| `tolerance` | the defensibility band. 🟡-vs-🟠 is a judgement call between reasonable people; ✅-vs-❌ is not. The metric must not punish defensible calls. |
| `basis` | the ground truth and where it comes from — a source URL, or the arithmetic shown |
| `rot` | `stable` (arithmetic, fixed-moment history — doesn't rot) or `dated` (present-tense claims about moving quantities). `review_by` in the case header says when dated labels need re-checking. Fixtures are dated readings too. |
| `pair` | id of a claim from the *same sentence* with the opposite truth value — the merge-behaviour metric ([#16](https://github.com/SerhiiKorniienko/bullshit-detector/issues/16)) needs at least one known pair per case |

**Corpus selection constraint** ([#41](https://github.com/SerhiiKorniienko/bullshit-detector/issues/41)):
a video quoted in the instruction files cannot measure the rule it illustrates —
`scripts/check-fixture-independence.py` includes `eval/cases/*/transcript.md` in its corpus,
so adding a fixture that collides with a worked example fails the repo check. `6mUScq-6U3U`
is burned for the fabrication-tell rule for exactly this reason and is deliberately not a case.

**Label provenance is stated, not implied.** `labeled_by` records who curated the labels and
whether the owner has reviewed them. The standing caveat from #3 stays attached: a harness
whose labels the tool's own author wrote narrows the "author-picked content" limitation, it
does not remove it.

**The corpus is checked, not trusted.** `uv run eval/check-cases.py` loads every case with the
scorer's own loader and asserts what a script can: each `quote` is a verbatim span of its
transcript (the gate's span check, so a quote the report gate would reject cannot be a
fixture identifier either), every labelled claim carries a `basis`, `tolerance` includes the
label, pairs point both ways, and dated labels have a `review_by`. It runs in CI. Whether a
label is *right* is the owner's review, which no script can do.

## The scorer

```
uv run eval/score.py cases/<id> <report.md> [more-reports.md ...]
uv run eval/score.py cases/<id> --stability <r1.md> <r2.md> ...
```

`score.py` is stdlib-only and offline — same rule as `tally.py`: the gate must be
deterministic and run anywhere. It reads claims from the report's `.claims.jsonl` sibling
when one exists (the `claim@1` file every run has written since 0.14.0), else parses the
markdown table with the same row shape the gate uses. When the file is there the `.md`
is never opened, which is what lets a claims-only run be scored at all.

Matching: normalized token-set similarity between the curated quote/claim and the report's
claim cell, greedy one-to-one, threshold auditable (`--min-similarity`; weak pairings under
0.75 are printed in the default output, every match with its score under `--json`).
Unmatched curated claims get a second pass against already-taken rows to detect merges,
and a merged claim's label is graded against the shared row's verdict — one verdict
claimed for two assertions is graded on both.

Metrics, all rates — counts are the thing run-to-run variance destroys:

1. **Extraction recall** — matched curated claims / all curated claims, overall and
   load-bearing-only. The number that settles "did 0.12.0 extract less" arguments in a
   minute instead of an afternoon.
2. **Extraction review queue** — report rows that matched no curated claim. Printed for
   human review, not auto-scored: an unmatched row is either padding (a precision failure)
   or a claim the curation missed (a curation failure), and only a person can say which.
3. **Verdict agreement** on matched labelled claims — exact, within-tolerance, a per-verdict
   confusion table, and quadratic weighted kappa over the ordinal ✅🟡🟠❌ axis (❓ is not on
   the truth axis and is reported separately). QWK because disagreeing by one step is not
   the same failure as disagreeing by four.
4. **Known-true confirm rate** — the release-gate number: of claims labelled `confirmed`,
   how many did the run rate within tolerance. Gate threshold `--threshold-true`, default
   0.95 per the spec on #3. "Never says false" shows up here as a specific number, not a vibe.
5. **Known-false catch rate** — of claims labelled `false`, how many the run rated
   misleading-or-worse.
6. **Merge behaviour** — when both members of a labelled `pair` land in one report row, the
   row's verdict must be at least as harsh as the pair's harshest label. A merged verdict
   gentler than its harshest part is verdict laundering and fails the gate.
7. **Stability** (`--stability`) — same case, N runs: per-claim verdict flip table, %
   unanimous, mean distinct verdicts per claim. The noise floor nothing has measured yet:
   every same-video comparison on record also changed version, model or harness.

Exit codes: `0` pass · `2` gate fail (known-true rate below threshold, or a laundered
merge) · `3` structural (unreadable case or report). Same convention as `tally.py`.

## Running a case

`eval/run-case.sh cases/<id> <outdir>` runs the full skill headless against the committed
transcript and scores the result. A full run costs 15–25 minutes of wall clock and real
model spend — the per-case cost is why the corpus starts small and why stage 2 below exists.

Method rules that are not optional, learned the hard way:

- **Blind runs only.** The runner must not be told what prior runs produced or shown
  `examples/`. Prior readings anchor; an anchored operator produced two false ❌ on this
  exact corpus.
- **Hand the runner the installed skill's paths.** A runner left to spelunk the repo spends
  ~170s patching around its environment and its gate cost measures the rig, not the tool
  (measured: −78% gate time when the paths are given).
- **Hold the harness fixed across arms.** Main-session opus and subagent sonnet are
  different instruments (11.3 vs 17.8 min median on identical work). A comparison that
  changes model, harness and release at once measures nothing.
- **The runner is never told it is being timed.** External instrumentation
  (`scripts/runprofile.py`) only.

### Claims-only runs

`EVAL_CLAIMS_ONLY=1 eval/run-case.sh cases/<id> <outdir>` asks the runner for the skill's
claims-only mode: full verification, then the claims file and its run record, and no
report. The script gates the file itself with `tally.py --claims --source <transcript>`
before scoring, so the reading does not depend on the runner having done so, and
`score.py` reads the file directly. This is a distinct arm, like quick mode: do not
compare a claims-only reading against a full-mode baseline as if they were one
instrument, even though the verification rules are identical, until the delta below
says they are.

`EVAL_SKILL=<dir>` points the run at a skill directory other than the installed symlink,
so a change can be measured from a worktree before it is linked.

**What it costs, measured.** The compose experiment
(`experiments/2026-08-08-compose-before-after.md`) already showed that dropping table
emission buys no wall time, because the clock is deliberation. Claims-only also drops the
prose sections, the gate rework on them and the render, and it buys no wall time either:
median 22.2 minutes full against 22.0 claims-only, n=3 per arm on `kospi-ai-bubble`,
ranges overlapping, quality inside the same band. The reading is in
`experiments/2026-09-02-claims-only-delta.md`. Use the mode because the claims file is the
only artifact the scorer reads, not because it is cheaper. It is not.

## Not built yet

- **Frozen evidence packs.** Caching source text per case so a prompt change is the only
  variable — the requirement (not optimisation) the credible-sources experiment established.
  Until then, verdict-agreement numbers carry retrieval noise and only large effects are
  readable.
- **Ablation configs.** Turn one rule off, re-run, measure what it was worth. Every rule
  shipped so far is justified by argument alone; this is what converts argument to evidence.
