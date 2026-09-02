# Does claims-only mode make a scored run cheaper? On the clock, no. On everything else, a little.

**Setup.** Six blind runs of the same video (`hy90LdpEUvQ`, the `kospi-ai-bubble` eval case),
one harness (`eval/run-case.sh`, sonnet, `effort: xhigh`, transcript pre-fetched, skill paths
handed over, runner never told it is timed), one variable: three runs in **full** mode (the
0.14.0 compose flow: claims file, shell, `--compose`, gate, render) and three in
**claims-only** mode (full verification, then the claims file and its run record, gated by
`tally.py --claims`, no report). Arms alternated full, claims, full, claims, full, claims so
time of day is spread evenly. Skill read from the PR branch at `b42a263`. Wall measured by the
driver around each `run-case.sh` call and, independently, by `scripts/runprofile.py` from the
transcripts; the two agree to within ten seconds on every run. Quality scored with
`eval/score.py` against the case's labels (drafts pending owner review, so the comparison
between arms is the readable part, not the absolute values).

The claim being tested is the one `eval/README.md` carried until this PR: that a scored case
does not need a prose report or a page, so a mode that stops at the claims file is what makes
a ten-case corpus affordable. The compose experiment
(`2026-08-08-compose-before-after.md`) had already found that dropping table emission bought
nothing, because the clock is deliberation. This is the same question one step further:
drop the prose sections, the gate rework on them and the render too.

## Wall clock and volume

| run | arm | wall | thinking | searches | output tokens | gate calls | N / M |
|---|---|---|---|---|---|---|---|
| 1 | full | 22.2m | 1047s (79%) | 44 | 117K | 4 | 37 / 30 |
| 2 | claims | 22.2m | 994s (75%) | 46 | 108K | 4 | 38 / 36 |
| 3 | full | 21.7m | 977s (75%) | 52 | 117K | 9 | 40 / 36 |
| 4 | claims | 22.0m | 976s (74%) | 47 | 110K | 12 | 40 / 36 |
| 5 | full | 25.3m | 1048s (69%) | 49 | 133K | 8 | 42 / 39 |
| 6 | claims | 18.8m | 788s (70%) | 49 | 90K | 4 | 34 / 31 |

Median wall **22.2m full, 22.0m claims-only**. Ranges 21.7 to 25.3 against 18.8 to 22.2,
overlapping. The fastest run of the six is a claims-only run and the slowest is a full run,
and the other four are indistinguishable. Median output tokens 117K against 108K, an 8% cut,
which is roughly the prose sections. Thinking share is unchanged at about three quarters of
the clock in both arms.

So the report is not where the time goes, for the third time of asking. The full arm spends
two to three minutes in compose and under ten seconds rendering; the claims-only arm gives
that time back to verification and to the gate. Run 4 is the clearest case: it spent 693
seconds, over half its wall, between its last search and its finished file, reading
`tally.py`'s source to learn the schema and writing a generator script that emitted every
claim in one batch at the end. That is the failure `CLAIMS.md` names (a file written in one
flush has the failure mode of the table it replaced) and the one `eval/README.md` warns
about (a runner left to spelunk measures the rig). It also tripped the gate once on
`readings: []`, which the validator now reads as null; the run had already worked around it.

## Quality, median of three per arm

| metric | full | claims-only |
|---|---|---|
| extraction recall | 0.800 | 0.750 |
| load-bearing recall | 0.786 | 0.750 |
| exact verdict agreement | 0.543 | 0.609 |
| tolerated agreement | 0.717 | 0.761 |
| QWK | 0.290 | 0.532 |
| known-true confirm rate | 0.700 (0.533 to 0.733) | 0.667 (0.567 to 0.733) |
| known-false catch rate | 0.5, 0.5, 1.0 | 0.5, 0.5, 0.25 |
| K10+K11 laundered merge | 3 of 3 | 2 of 3 |
| stability, unanimous claims | 23 of 60 | 31 of 60 |
| stability, mean distinct verdicts | 1.68 | 1.62 |

Nothing here separates at n=3. Recall leans full, agreement leans claims-only, the gate
number is a wash, and the two arms swap the best and worst single runs between metrics.
The one reading worth carrying forward is that the claims-only arm is not a *laxer*
instrument: its quote check ran on every run, its known-true rate sits inside the full arm's
range, and the laundered K10+K11 merge appears in both arms. The full arm's three readings
also sit inside the compose experiment's sonnet band from four weeks earlier (known-true
0.7 to 0.833, recall 0.733), so the corpus is behaving like the same corpus.

Every run failed the eval gate. Known-true 0.95 is the threshold and no run came within
0.2 of it. That is the number the corpus is for, and it is published here as read.

## What claims-only buys, then

- **Nothing on the clock.** Do not budget a corpus on it. The lever that moves wall time
  remains the effort setting, and that is a different instrument, not a cheaper reading of
  this one.
- **The scored artifact and nothing else.** `score.py` never opens the `.md` when the
  claims file exists, so a scored run that also writes prose, gates it against the source
  and renders a page is producing three artifacts the scorer never reads. Fewer artifacts
  is fewer things that can disagree, and the compose experiment found that class of bug on
  a published page.
- **The same gate.** `tally.py --claims` runs the line validation and the quote check the
  report gate would have run. A claims-only run that skipped that would be a weaker
  measure of the thing being measured, which is why it shipped in the same PR.
- **About 8% fewer output tokens**, which is real spend and not wall.

## Verdict

Keep claims-only as the eval arm, for the artifact reason and not for speed. Every
statement that a mode "makes the corpus affordable" should now be read as a prediction the
repo has tested three times and found false three times. Runs that batch the claims file at
the end are a wording problem in SKILL.md step 4, not a mode problem, and they happened in
both arms.
