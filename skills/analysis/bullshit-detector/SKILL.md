---
name: bullshit-detector
description: Fact-check and hype-audit content. Extracts the discrete claims from a video, article, tweet, or PDF, verifies each against independent sources via web search, and produces a report card with per-claim verdicts and an overall BS score (0-10). Use when the user asks to fact-check, verify, debunk, or evaluate credibility — "is this true/legit/bullshit", "check this video", "how much of this holds up".
---

# bullshit-detector

Separate what's verifiably true from what's hype in any piece of content.

## Workflow

1. **Get the text.** If the input is a URL and the `fetch-content` skill is installed, use its script. Otherwise use your web fetch tool or ask the user to paste the content. Keep the metadata (views, author, date) — it feeds step 5.
2. **Read the whole thing** before judging anything. Note the author's incentive: what are they selling, and where does the content funnel the audience?
3. **Extract claims.** List every distinct claim and classify each: `factual` (checkable now), `prediction`, `opinion`, `anecdote` (personal story, unverifiable by definition). Number them with source timestamps/locations.

   **One claim = one assertion a single search could settle.** Granularity is not a free choice: it sets the denominator every ratio in the report is built on, and two runs that slice the same content differently are not comparable. So:

   - **Don't split** one assertion into parts that would share a search. "$3–4T poured in, mostly debt" is *two* claims only because the spend figure and the debt share need different sources — "$3–4T poured in during 2020–2026" is one, not three.
   - **Don't merge** two facts that need separate sources just because they share a sentence.
   - **Don't extract framing as fact.** Definitions ("a token is roughly a word"), scene-setting and rhetorical asides are not claims the content is staking anything on; listing them pads the denominator and makes the content look better-sourced than it is.
   - **Rank by load-bearing weight, not order of appearance.** The reader needs to know which claims the thesis dies without.

   **Then pin each claim down, and drop the ones you can't.** A claim whose meaning isn't fixed is a claim you will check against a guess — and the report will show no trace of the guess.

   - **Resolve the referents from the surrounding content.** "They said it would double next year" isn't checkable until *they*, *it* and *next year* are fixed. Two things block this: *referential* ambiguity (unclear what a word points to) and *structural* ambiguity (the grammar allows two readings — "AI advanced renewable energy and agriculture at Acme and Globex" can mean both at both, or one at each).
   - **Vagueness is not ambiguity.** "Some experts", "involved in", "the early days" are vague but unambiguous. They stay, and they get checked as stated. Do not "resolve" a vague claim into a sharper one the speaker didn't make — that is the same error in the other direction.
   - **If the content doesn't resolve it, drop the claim** — even when the rest of the sentence is checkable. The test: would readers given this same content converge on one reading? If they wouldn't, you are about to pick one and attribute it to the speaker. Dropping loses a row; guessing invents a claim and then fact-checks it, which is the worse failure by a distance.
   - **Undefined is not ambiguous — never drop a claim for inventing its own terms.** "Consistency builds algorithm authority over time" can't be pinned down, but not because the content left something unsaid: "algorithm authority" denotes nothing. Ambiguity means the content has a meaning you can't determine; invention means there is no meaning to determine. Dropping the second makes the invention the reason the invention goes unreported, which is backwards — it keeps a row, and the missing referent *is* the evidence. See the fabrication tells in [RUBRIC.md](RUBRIC.md). Same for a claim that is simply false: unpinnable and untrue are different findings, and only one of them is a reason to stop looking.
   - **Write every surviving claim so it stands alone**, with the missing context in square brackets: `The [Boston] council expects its law [banning plastic bags] to pass in January 2025`. A reader must be able to re-check row 7 without having read rows 1–6 or watched the video. This is what makes the claims table independently checkable rather than a set of notes about the content.
   - **Dropped claims are not table rows and do not count toward `N`.** They are reported as a count next to the tally, with a word on what they were. A content full of assertions nobody can pin down is itself a finding — say so in the bottom line when the count is high.
4. **Verify.** First split the factual claims into **load-bearing** (the thesis collapses without them, including any claim *derived* from them) and **incidental**. Then:

   - **Verify every load-bearing claim, however many there are.** There is no cap on these. If the argument rests on twelve interlocking numbers, checking ten of them produces a report that cannot support its own conclusion.
   - **Verify incidental claims as budget allows**, most consequential first. Anything you don't reach is `⚪ not checked` — never a guess.
   - **If you cannot verify a load-bearing claim**, say so prominently in the bottom line. A thesis with an unchecked load-bearing premise has not been audited, and the report must not imply otherwise.

   For each claim you do check, web-search for independent evidence and rank what you find against the source hierarchy in [RUBRIC.md](RUBRIC.md) — empirical and primary sources first, interested parties last. Before calling a claim corroborated, **collapse syndicated results to their origin and count origins, not URLs** (RUBRIC.md has the tells).

   **One search is a first attempt, not a verdict.** When what came back doesn't clear the bar in [RUBRIC.md](RUBRIC.md) ("When is the evidence enough?"), don't settle for it — say what's missing and go get that:

   - **Name the gap in words before searching again.** "Found the figure repeated everywhere, never the study it comes from." "Nothing dated after the 2024 revision." "Only the company's own blog." A named gap produces a targeted query; "search again" produces the same results twice.
   - **Change the angle, not the wording.** A rephrase of a query that failed usually fails again. Go at it from a different direction: the primary document rather than coverage of it, the regulator rather than the press, the original language, the date range, or the claim's opposite.
   - **Search for what would refute it, not for more of what you have.** A fourth URL agreeing with the first three usually shares their origin and changes nothing. The follow-up search exists to find what would move the verdict.
   - **Cap it and say so.** Two follow-ups per claim, three for load-bearing ones, then stop. A claim that exhausts the budget is ❓ unverifiable **with the gap named** — "searched three angles; the underlying study was never located" tells a reader something a bare ❓ doesn't, and tells the next run where to start.

   If the `coverage-check` skill is available, **run it on any claim whose corroboration rests on breadth of coverage** — where you are about to write "widely reported" or cite four or more URLs for one fact. Those are the claims where eyeballing fails and a measured origin count changes the verdict. Skipping it is fine for a claim resting on one primary document; skipping it on "everyone reported this" is the error it exists to prevent. If it returns exit 3, the measurement is unavailable — fall back to the tells and say the count is an estimate. Assign a verdict (scale below) and cite what you found, naming the tier when it's doing the work. Never rate a claim `confirmed` or `false` on memory alone — verdicts need sources.
5. **Scan for hype signals** using the checklist in [RUBRIC.md](RUBRIC.md).
6. **Write the report card** using the template in [RUBRIC.md](RUBRIC.md), ending with the 0-10 BS score.

7. **Save it to a file, always.** The file is the artifact — it survives the session, it can be diffed against a later run, and it is what gets published.

   - Write the complete markdown to `/tmp/bs-report-<slug>-<YYYY-MM-DD>.md`, where `<slug>` is a short kebab-case form of the content's title (`bs-report-claude-situation-shitshow-2026-07-30.md`). On a system without `/tmp`, use the platform temp directory.
   - **Never overwrite.** If the path exists, append `-2`, `-3`, … Re-running the same content on the same day produces a *second* reading, and comparing them is the point — silently clobbering the first destroys the evidence that verdicts move between runs.
   - **Always end your reply with the full file path on its own line**, whichever output mode you used.
   - If writing fails, say so plainly and print the report inline rather than losing it.

   Then **check it with the script — do not count the table by hand**:

   ```bash
   uv run scripts/tally.py <the-file-you-just-wrote>
   ```

   It recounts every row, rebuilds the tally line, and verifies the version stamp, the linked source, the origin markers and the claim numbering. Exit 2 means the report is non-compliant: fix what it names and re-run until it exits 0. `--fix` rewrites the tally line in place.

   This is not belt-and-braces. Counting a 40-row table by eye failed in three consecutive real runs — off by 2, then by 8 — while the analysis itself was sound. Attention goes to the argument and the bookkeeping silently rots, so the bookkeeping is the script's job now.

   End the report with the run line from [RUBRIC.md](RUBRIC.md) — one italic line, counting the searches you issued, the tool calls you made, the `coverage-check` runs, the wall time since step 1, and the wall time divided by `M`. It is the only cost figure a reader sees.

   Then write a run record beside it — same path with `.md` swapped for `.run.json`:

   ```json
   {"schema": "bullshit-detector/run@1", "version": "<same stamp the report carries>",
    "source": "<url or file>", "report": "<report path>",
    "started": "<ISO time from step 1>", "finished": "<ISO time now>", "wall_seconds": 722,
    "claims": {"extracted": 28, "checked": 23, "dropped_ambiguous": 2},
    "fetches": 1, "coverage_checks": 0,
    "queries": [{"claim": 3, "pass": "first", "q": "the query, verbatim"},
                {"claim": 3, "pass": "follow-up", "q": "the next angle, verbatim"}]}
   ```

   **This never appears in the report.** A reader wants to know whether the content is true, not what it cost to find out. The record exists so runs can be compared across releases — `scripts/runstats.py` reads them — and so the follow-up searches in step 4 can be checked afterwards for whether they genuinely changed angle or just reworded. Log each query as you issue it, including the ones that return nothing; a list rebuilt from memory at the end is wrong in the direction that flatters the run.

   If you can't write it, skip it silently. It is diagnostic, and no part of the report depends on it.

8. **Print the full report by default.** Reproduce the whole card in the reply — claims table included — unless the user asked for something shorter.

   Switch to a summary only when they signal it ("short version", "just the score", "TLDR", "summary only", or a standing instruction to keep output brief). A summary is: the source line, the BS score and its one-line verdict, the tally, the two or three findings that actually matter, and the file path.

   Don't offer the choice up front or ask which they want — print the full report and let them ask for less. They already have the path either way.

## Checking your own draft before you publish

The workflow runs on any text, including text the user wrote themselves — a blog post, a launch
announcement, a README, a pitch deck, a thread. When someone asks you to check their own draft,
skip steps 1–2 (you already have the text, and the incentive analysis is theirs), then run claim
extraction and verification exactly as normal.

Two adjustments:

- **Report before they publish, not after.** Flag the claims that won't survive a reader checking
  them, and say which source would fix each — a stale figure with a current one next to it is
  more useful than a verdict.
- **Don't soften it because it's theirs.** A draft audit that grades on a curve is worthless; the
  whole value is finding what a hostile reader would find first.

## Long content

For transcripts over ~10,000 words (feature-length videos, podcasts, long interviews):

- Split the transcript into 4–6 chunks and, if your harness supports subagents or parallel tasks, fan claim extraction out across them — one chunk per task, each returning claims with timestamps, speaker, and type. Extraction is mechanical: if your harness lets you pick a model per task, a small/fast model is fine here (the Claude Code plugin bundles a `claim-extractor` agent preconfigured for this).
- Merge and dedupe the extracted claims, then select the load-bearing ones as usual.
- Verification of independent claims can also run in parallel.
- No subagents available? Process sequentially — the workflow is identical, just slower.

## Verdict scale

| Verdict | Meaning |
|---------|---------|
| ✅ confirmed | Independent sources support it |
| 🟡 plausible | Consistent with evidence, not directly confirmed |
| 🟠 misleading | Kernel of truth, framed to deceive (cherry-picked, outdated, exaggerated) |
| ❌ false | Contradicted by evidence |
| ❓ unverifiable | No way to check (private data, anecdote, vague) |
| ⚪ not checked | Extracted but outside the verification cap — **no verdict claimed** |

## Judgment rules

- Distinguish "this claim is false" from "this claim is unproven" — don't inflate verdicts in either direction.
- **You check premises, not reasoning.** A false fact gets caught; a valid-looking inference drawn from true facts does not. If the content's conclusion doesn't follow from its own claims even though every claim checks out, say that explicitly in the bottom line — the per-claim table will not show it.
- **Checking arithmetic is not confirming a claim.** If a figure follows correctly from inputs the content supplied, you have verified its calculator, not the world. Rate it on whether the *inputs* survive: sound inputs and sound arithmetic is ✅; sound arithmetic on inflated inputs is 🟠 misleading, however clean the sum. Never award ✅ for internal consistency alone — say "arithmetic checks out" in the evidence cell and let the input's verdict carry the row.
- **A specific claim with no footprint is not the same as a private one.** "Our internal revenue tripled" is unverifiable because the data is private, which is expected. A named framework, award, certification, case number, study or affiliation that returns *nothing* is a different finding — the content chose a checkable referent and there is no trace of it. Both are ❓, but the second says "no record found", counts as the fabrication tell in [RUBRIC.md](RUBRIC.md), and gets called out by name in the bottom line. Only fire it when your searches are demonstrably working — a search returning nothing at all is broken, not evidence.
- **Unreachable ≠ unverifiable.** If the evidence trail dead-ends at a paywall, a blocked domain, or a dead link, rate the claim ❓ unverifiable *and say the evidence exists but you couldn't reach it*. That is a different failure from a claim nobody has ever checked, and the reader needs to tell them apart.
- Predictions are not lies; judge them on whether the stated reasoning holds and whether the speaker hedges honestly.
- An anecdote used as proof of a general pattern is a hype signal even when the anecdote itself is true.
- High production value, confidence, and view counts are not evidence of anything.
- Steelman first: check whether a generous reading of the claim survives before rating it `misleading` or `false`.
- If the content is mostly solid, say so plainly — the tool detects bullshit, it doesn't manufacture it.
- Write the report in the user's language, whatever language the content is in. Keep quoted claims in the original language when the wording itself is the evidence, with a translation if the languages differ.
