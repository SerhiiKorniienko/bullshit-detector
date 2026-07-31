# Does telling it to "use credible sources" help?

**Run:** 2026-07-30 · **Tool version:** v0.4.2 · **Closes:** [#4](https://github.com/SerhiiKorniienko/bullshit-detector/issues/4)

On the [Show HN thread](https://news.ycombinator.com/item?id=49096917), [simonw](https://news.ycombinator.com/user?id=simonw) said:

> Telling ChatGPT to "use credible sources" — you can watch its thinking trace and see it rule out
> random blogs, consider media publications with a good reputation for fact checking, and
> double-check information that seems unlikely.

I said I'd test it and publish the comparison. This is that, and the result is not the one I
expected: **the experiment I designed cannot answer the question, and while trying to run it I
found something that matters more.**

Both halves are below. The negative result is not buried.

---

## TL;DR

1. **A large share of the outlets simonw is describing are unreachable.** Reuters, AP, WSJ, FT,
   NYT, Guardian, Economist, Atlantic, New Yorker, Politico, Wired, The Verge, Ars Technica, BBC,
   Business Insider and ZDNet all refuse this agent's crawler. You can instruct the model to prefer
   reputable news all day; that tier is largely missing from the pool it draws on.
2. **Their reporting still arrives — laundered.** The WIRED and Business Insider figures for one
   claim reached the tool anyway, quoted secondhand by aggregators. The tool would have cited the
   aggregator as an independent source. That is [#1](https://github.com/SerhiiKorniienko/bullshit-detector/issues/1)
   with a reproducible instance.
3. **The run-to-run noise is larger than the effect I was trying to measure.** The same query, same
   day, minutes apart, returned an 11%-overlapping source set and *lost the evidence a published
   verdict depends on*.
4. So: **no, I can't tell you whether "use credible sources" helps.** Not because it doesn't —
   because this tool has no instrument capable of detecting it. That's
   [#3](https://github.com/SerhiiKorniienko/bullshit-detector/issues/3), and it just became the
   top of the backlog.

---

## What I ran

**Subject:** [the Dan Martell report](../examples/0.4.x/report-14-ways-to-make-money-with-ai.md) —
YouTube, 1,164,773 views, published BS score 5/10. Picked because business/AI-market claims are
where content-marketing blogs pollute results hardest. The astronomy report would have been a weak
test: NASA dominates that result pool no matter how you ask.

**Scope:** the 7 factual claims (#1–#7). Verification is the only step the instruction modifies,
and it only acts on factual claims. The other five are opinion, prediction or anecdote — including
them would have padded the sample with guaranteed no-ops.

**Arms:**

| Arm | Instruction |
|---|---|
| **A** | current `SKILL.md` step 4 verbatim — *"prefer primary sources (papers, official docs, filings, reputable reporting) over content marketing"* |
| **A′** | identical to A, re-run. The noise floor. |
| **B** | A, plus simonw's instruction |

A′ is the arm that made this worth doing. Without it, any A-vs-B difference is uninterpretable.

---

## Finding 1 — the noise floor swallows the experiment

Claim #1 (*"Renaissance, D.E. Shaw, Two Sigma are only trading the employees' money"*), same query,
minutes apart:

| Arm A returned | Arm A′ returned |
|---|---|
| techinterview.org | bogleheads.org (forum) |
| rupakghose.substack.com | financhill.com |
| danielscrivner.com | quantifiedstrategies.com |
| wallstreetoasis.com (forum) | quartr.com |
| pyrfordfp.com | ofdollarsanddata.com |
| brokersdb.com | **en.wikipedia.org** |
| waylandz.com | medium.com |
| brunch.co.kr | moneysexnerd.com |
| | brunch.co.kr |

**One domain of nine in common.** Worse than the churn: arm A′ *lost the evidence the verdict rests
on*. The published 🟠 misleading verdict depends on knowing that D.E. Shaw and Two Sigma manage large
external capital. Arm A′ came back with, in its own words, "the search results do not contain any
information comparing… D.E. Shaw or Two Sigma." Same tool, same query, same day — one run can
support the verdict and the next cannot reach it.

The churn is also wildly uneven. Claim #6 returned a **byte-identical** result set across arms.
Claim #1 turned over almost completely. So there isn't a stable "noise level" to subtract; it's
per-query and unpredictable.

Any honest reading: an A-vs-B difference of the size I could plausibly detect across 7 claims is
indistinguishable from this.

## Finding 2 — the credible tier is largely unreachable

I tried to pin arm B to reputable outlets. The tool refused, and named why:

```
API Error: 400 The following domains are not accessible to our user agent:
['ft.com', 'reuters.com', 'wsj.com']
```

Probing systematically:

**Blocked** — Reuters · AP · WSJ · FT · NYT · Guardian · Economist · Atlantic · New Yorker ·
Politico · Wired · The Verge · Ars Technica · BBC · Business Insider · ZDNet

**Reachable** — every `.gov` and official source tried (SEC, FTC, DoJ, NASA, NIH, WHO, europa.eu,
gov.uk) · journals (Nature, Science, ScienceDirect, arXiv, PubMed) · **every dedicated fact-checker
tried** (Snopes, PolitiFact, FactCheck.org, FullFact) · Wikipedia · WaPo · NPR · Bloomberg · CNBC ·
Forbes · Time · ProPublica · Axios · TechCrunch · The Information · 404 Media · The Register

The pattern is specific and consequential. **Primary and official sources are fine. Dedicated
fact-checkers are fine. General news with the strongest fact-checking reputations is the one tier
that's been hollowed out** — and it is exactly the tier simonw's instruction targets.

This is a property of the harness, not of the instruction. It is also *agent-specific*: a different
harness has a different blocklist, so the same skill produces different source quality depending on
what runs it. For a repo that ships to any agent, that's a portability problem I hadn't considered.

What fills the vacuum, from arm A's actual results: SEO affiliate blogs, vendor content marketing,
a paid press-release wire, a Wall Street forum, an AI-generated wiki, and — for the claim about the
speaker's own revenue — **the speaker's own podcast and website, exclusively.** Across all 7 claims
in arm A, the number of tier-2 reputable-news sources retrieved was **zero**.

## Finding 3 — blocked reporting arrives laundered, and counts as independent

Claim #2 concerns rentahuman.ai's user numbers. WIRED and Business Insider both reported figures.
Both are blocked. The figures reached the tool anyway:

> "Business Insider reported about 200,000 signups in a week, while WIRED reported 518,284
> registered humans."

— retrieved from aggregator pages quoting them, alongside the platform's own marketing boast that
it "was featured in Forbes, Wired, Futurism, and 30+ more publications."

So the tool ends up with WIRED's number, no access to WIRED's article, and a citation pointing at
whoever quoted it. Under v0.4.2's counting that reads as an independent corroborating source. It
is not one — it's one outlet's reporting wearing an aggregator's URL, which is precisely the gap
[mtweak flagged](https://github.com/SerhiiKorniienko/bullshit-detector/issues/1). The blocklist
doesn't just remove good sources; it actively manufactures the syndication problem.

For the record, the claim's numbers remain a mess across every arm: 700k, 650k, 518,284, 500k,
200k, 110k, 70k+, against ~83 verifiable active profiles. The published 🟠 misleading verdict holds.

## What did change in arm B

Reported for completeness, **not** as a measured effect — per Finding 1, none of this clears the
noise floor:

- Claim #1: arm B surfaced Wikipedia, a Harvard case study and CB Insights, and **recovered the
  D.E. Shaw/Two Sigma evidence arm A′ had lost**. It also produced a sharper number than the
  published report used — Medallion capped at ~$9–10B against Renaissance's >$106B total AUM,
  which strengthens the 🟠 misleading verdict rather than changing it.
- Claim #2: arm B surfaced the **Y Combinator company profile** — primary, and absent from arm A.
- Claim #4: arm B reached Stripe's and OpenAI's own docs, and confirmed AP2 is Google's separate
  competing protocol with 60+ partners. Same verdict as published, better sourced.

**No verdict flipped in any arm.** All 7 claims held their published verdicts wherever the evidence
was reachable at all.

Arm B's queries were also *shaped* differently by the instruction, not just filtered — so it varies
from A on two axes at once. That's realistic (it's what a real run does) and it's another reason
the comparison can't be cleanly attributed.

---

## Limitations, stated plainly

- **Not blinded.** One operator, who had read the published report and knew its verdicts before
  starting. Every arm is anchored by that.
- **n = 7 claims, one piece of content, one model, one day.** No statistical claim is available and
  none is made above.
- **Search retrieval is non-deterministic and moves under you.** That was supposed to be a
  controlled-for nuisance. It turned out to be the headline.
- The blocklist finding is the one result here that is **deterministic and reproducible** — anyone
  can re-run the probe and get the same answer. Treat the rest as observation, not measurement.

## What changes because of this

- **[#3](https://github.com/SerhiiKorniienko/bullshit-detector/issues/3) (eval harness) is now the
  top of the backlog.** Every accuracy question routes through it. This run is the proof: without a
  held-out labelled set and repeated trials, the tool cannot answer questions about its own
  behaviour, including easy ones.
- **[#2](https://github.com/SerhiiKorniienko/bullshit-detector/issues/2) (source hierarchy, empirical
  first) gains a second justification.** mtweak argued primary sources are epistemically better. This
  says they're also *the tier that's actually reachable*. Ranking reporting at the top would be
  ranking on availability the tool doesn't have.
- **[#1](https://github.com/SerhiiKorniienko/bullshit-detector/issues/1) (syndication collapse) is
  worse than assessed.** It isn't only wire copy across ten outlets — it's blocked reporting
  re-emerging through aggregators, where the original is *unreachable by construction*.
- **New, unfiled:** report a claim's evidence as unreachable rather than silently substituting
  whatever ranked next. Right now a blocked source and a nonexistent one look identical from inside
  the tool.

## Reproducing this

Everything above is re-runnable. The blocklist probe is the cheap part — ask any agent with web
search to restrict a search to `reuters.com` and read the error. The noise-floor measurement is
just the same query twice, diffed. If you get a different answer than I did, that is itself worth
knowing, and the issue thread is open.
