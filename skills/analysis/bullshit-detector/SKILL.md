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
4. **Verify.** Take the factual claims — all of them if ≤10, otherwise the ~10 most load-bearing (the ones the content's thesis depends on). For each, web-search for independent evidence; prefer primary sources (papers, official docs, filings, reputable reporting) over content marketing. Assign a verdict (scale below) and cite what you found. Never rate a claim `confirmed` or `false` on memory alone — verdicts need sources.
5. **Scan for hype signals** using the checklist in [RUBRIC.md](RUBRIC.md).
6. **Write the report card** using the template in [RUBRIC.md](RUBRIC.md), ending with the 0-10 BS score.

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

## Judgment rules

- Distinguish "this claim is false" from "this claim is unproven" — don't inflate verdicts in either direction.
- Predictions are not lies; judge them on whether the stated reasoning holds and whether the speaker hedges honestly.
- An anecdote used as proof of a general pattern is a hype signal even when the anecdote itself is true.
- High production value, confidence, and view counts are not evidence of anything.
- Steelman first: check whether a generous reading of the claim survives before rating it `misleading` or `false`.
- If the content is mostly solid, say so plainly — the tool detects bullshit, it doesn't manufacture it.
- Write the report in the user's language, whatever language the content is in. Keep quoted claims in the original language when the wording itself is the evidence, with a translation if the languages differ.
