# Sourcing, hype signals & report card

## Source hierarchy

Rank every source you cite. When sources disagree, the higher tier wins unless you can say why it
shouldn't. When the best you can reach is tier 4 or 5, the verdict is capped at 🟡 plausible or
❓ unverifiable — never ✅ confirmed.

| Tier | What it is | Examples |
|---|---|---|
| **1 — Empirical / primary** | The thing itself, or a direct record of it | Filings, court records, official docs and changelogs, datasets, papers, the actual video/photo/receipt, public disclosures at source |
| **2 — Reporting with a corrections desk** | Outlets with a fact-checking reputation and a published corrections policy | Established news organisations, dedicated fact-checkers |
| **3 — Trade / niche reporting** | Credible but narrow, usually no corrections desk | Industry press, specialist newsletters, analyst notes |
| **4 — Interested party** | Accurate about itself at best, marketing at worst | Vendor blogs, press releases, the subject's own site/podcast/PR, affiliate and SEO content |
| **5 — Unattributed** | No accountable author | Forums, aggregators, content farms, AI-generated wikis |

Two rules that do the work:

- **Empirical beats eloquent.** A filing that is boring and hard to read outranks a well-written
  article about the filing. If the article's claim traces back to a document, cite the document.
- **A source about itself is tier 4, whatever its usual tier.** A company's own numbers for its own
  product are marketing even when published by a reputable outlet quoting the press release. Say
  so in the evidence column: "the platform's own figure".

### Tier the document, not the domain

The rule above has a second form that catches far more results: **sponsored, branded, partner and
advertorial content carries the advertiser's tier, not the publisher's.** It is the advertiser
talking about itself, printed under a masthead it paid for. Tier 4, and name it —
`[tier 4: FT partner content, paid for by Comarch]`.

This is not an edge case. Restricting search to reputable domains and reading the top twenty results
returned **five** advertorials and index pages, every one of which reads as tier 2 if you tier by
domain (see [experiments/](../../../experiments/2026-07-30-search-api-access.md)):

```
reuters.com/media-campaign/brandfeatures/medc/...    branded content
theatlantic.com/sponsored/deloitte-shifts/...        sponsored
sponsored.bloomberg.com/immersive/globalx/...        sponsored subdomain
ft.com/partnercontent/comarch/...                    "paid for and produced by Comarch"
```

Restricting to reputable domains *raises* the share of these, because that is where the advertising
budget goes. The signal is usually in the URL and almost always in the page:

- **URL path** — `/sponsored/`, `/partnercontent/`, `/partner-content/`, `/brandfeatures/`,
  `/branded/`, `/paid-post/`, `/paidpost/`, `/media-campaign/`, `/advertorial/`, `/promoted/`
- **Subdomain** — `sponsored.*`, `partners.*`, `paidpost.*`
- **On the page** — "paid for and produced by", "sponsored content", "brand feature",
  "in partnership with", "advertisement feature", "promoted by", "presented by"

**A tier-4 ceiling means a tier-4 verdict cap**: the rule at the top of this file already caps a
claim at 🟡 plausible when the best reachable source is tier 4. Advertorial corroboration does not
make a claim ✅ confirmed, however reputable the masthead above it.

Two things this rule is *not*. It is not a judgement about accuracy — sponsored content is often
factually correct, and the tier is about who is accountable for it, not whether it is wrong. And it
does not apply to ordinary journalism that merely quotes a company; that is already covered by
"a source about itself", one row up.

### Reachability is not credibility

Some high-reputation outlets block agent crawlers, so they never appear in your results — their
absence is not evidence that no one reported the claim, and the SEO blog that ranked in their place
is not the best available source, only the best *reachable* one. If a claim's evidence trail dead-ends
at a paywall or a blocked domain, say the evidence was unreachable. Do not silently substitute
whatever ranked next. See [experiments/](../../../experiments/2026-07-30-credible-sources.md) for how
badly this skews the pool in practice.

## Counting sources: collapse syndication first

Ten URLs are not ten sources. Before you describe a claim as independently corroborated, collapse
everything that traces back to one origin into a single source, and count origins.

Signs that several results share one origin:

- **Explicit attribution** — "according to Reuters", "the AP reported", a bylined wire credit
- **Near-identical phrasing**, especially identical quotes, identical figures to the same odd
  precision, or the same unusual turn of phrase
- **Timing cluster** — a run of pieces within hours of each other after a press release or embargo lift
- **All roads lead to one document** — every result cites the same study, filing or announcement
- **Laundered reporting** — an aggregator quoting an outlet you couldn't reach. That is still the
  blocked outlet's reporting; credit it to them, at their tier, and note you couldn't read the original

State the count honestly in the evidence column: "4 results, 1 origin (all quoting the same company
press release)" is worth more than a list of four links. **One origin corroborating itself across ten
outlets is one source, and a claim resting on it cannot be ✅ confirmed on volume alone.**

Independence means *separate access to the underlying facts* — a second newsroom that made its own
calls, a regulator that ran its own audit, a researcher with their own data. Not a second URL.

The tells above are eyeball heuristics. If the `coverage-check` skill is available, it measures the
same thing — it groups coverage into story clusters and flags publication bursts, so you get an
origin count rather than an impression. Its 3-month window is the catch: an empty result there means
"outside the window", never "unreported".

**It is not the usual way to get an origin count, though — reading your own results is.** When four
URLs are in front of you and all four cite the same filing, collapsing them yourself costs nothing
and lets you name the origin, which tells a reader more than a number does. Save the measurement for
the claim that rests on breadth you cannot inspect, and run it once per report rather than once per
row (SKILL.md step 4 has the cost that forces this). **Say which kind of count it is** when the
distinction could matter: a measured origin count and one judged from the tells are different
evidence, and a report that presents the second as the first is doing the thing this tool exists to
catch.

## When is the evidence enough?

Before assigning a verdict, check what you have against these. They are the bar SKILL.md step 4
loops against — miss one and the answer is another search, not a softer verdict.

- **It addresses the claim, not its neighbourhood.** Evidence that the company exists, or that the
  topic is real, is not evidence for the specific assertion being checked.
- **It is the best tier reachable for a claim of this kind.** A figure sourced only to the party
  it flatters has not been checked, it has been repeated. If a primary document would settle it and
  you haven't looked for the document, you aren't done.
- **It is current with respect to the claim.** A superseded filing, a pre-revision guideline or a
  price from two years ago answers a question nobody asked.
- **Nothing credible contradicts it unresolved.** A contradiction from a source at the same tier or
  higher has to be addressed, not omitted.
- **Corroboration is counted in origins.** See the syndication rules above: repetition is not
  independence, and volume never substitutes for tier.

**There is deliberately no minimum source count here.** One tier-1 primary document settles a claim
that five tier-3 mentions cannot, so a numeric threshold ("three or more sources") would demand
padding on the claims that are best evidenced and permit thin agreement on the ones that aren't.
The hierarchy already answers the question a count is trying to approximate.

When it still doesn't clear the bar after the follow-up searches SKILL.md allows: ❓ unverifiable,
with the gap named. That is an honest answer. A ✅ built on the best of a weak pool is not.

## Hype-signal checklist

Count how many apply. Each is a signal, not proof — the report should name the ones observed with examples.

**Language**
- Urgency/scarcity: "before it's too late", "window is closing", "99% of people don't know this"
- Absolutes: "guaranteed", "never fails", "the only way", "nobody is talking about this"
- Unrealistic specificity: "$11,347 in my first month" (precise numbers imply rigor without providing it)

**Structure**
- Claims of easy money/results with no mention of failure rates, competition, or time investment
- Anecdote (n=1) presented as a repeatable system
- Social proof substituting for evidence: views, follower counts, screenshots of dashboards
- Credential claims that can't be verified or are irrelevant to the topic

**Incentive**
- The content funnels to a paid product: course, community, coaching, affiliate links, "link in bio"
- The speaker profits from the audience *believing* the claim, independent of the claim being true
- Success attributed entirely to the method being sold, never to timing, capital, or audience the speaker already had

**Evasion**
- No sources, or sources that trace back to the speaker themselves
- Hedge-free confidence about the future
- Preemptive dismissal of skeptics ("haters", "broke mindset")

**Fabrication tells**
- A named specific with no footprint at all: a framework, award, certification, case or reference
  number, study, or affiliation that returns *nothing* — not thin coverage, nothing
- Credentials attached to real institutions that the institution itself has no record of
- A public figure or statistic presented as the speaker's own result
- Precision that rises as checkability falls: exact numbers about things nobody else can see

**An invented term is a fabrication tell, not an ambiguous claim.** A claim built on a construct that
denotes nothing — "algorithm authority", a proprietary-sounding metric no one else uses — reads as
unpinnable, and step 3's disambiguation gate will drop it unless told otherwise. It must not: the
absent referent is the finding, and dropping the row means the invention is why the invention goes
unreported. Keep the row, and say the term has no definition outside this content.

This group inverts the usual reading of specificity. "Our TrustFrame™ methodology, used by 340+
organisations, delivered a 340% improvement under reference NHS-2024-AI-0891" sounds more rigorous
than a vague version of the same boast, and scores better with any reader — human or model — who
treats detail as evidence. It is also easier to check, and that is the point: a real framework, a
real award and a real case number leave traces, and an invented one leaves none.

Two guards, because this signal fails in a specific direction:

- **Only fire it when the search is working.** Zero results because a domain blocks the crawler,
  because the entity is non-English, or because it predates the searchable web is not a fabrication
  tell — it is the reachability problem above wearing a disguise. The test is whether searches
  return *other* things: a working search that finds everything except this is evidence; a search
  that finds nothing at all is a broken search.
- **This is never proof of invention.** You cannot verify nonexistence. The verdict stays
  ❓ unverifiable with "no record found" in the evidence cell — but unlike other ❓ rows, it counts
  as a signal, because the content chose to assert something checkable and there was nothing there.

The misattribution case is different and rates differently: a real public statistic presented as the
speaker's own result is 🟠 **misleading**, not unverifiable. The number is fine. The attribution is
the claim, and it is false.

## BS score (0–10)

**The score covers what you checked, and nothing else.** A `⚪ not checked` claim must not move it in
either direction — not up because something looked shaky, not down because the rest held up. If the
unchecked remainder is large enough that a reader might reasonably reach a different score, say so
next to the number rather than letting it imply full coverage.

**The one ❓ that does move the score** is the fabrication tell above: a named, checkable specific
with no footprint, where the search was demonstrably working. That is not a statement about the
evidence available to you — the content picked the referent, and picked one that isn't there. It
counts as a signal like any other, and it counts harder when the claim is load-bearing.

**Never raise the score because sourcing was poor.** A 🟡 that means *"this is probably true but the
only reachable source was a vendor blog"* is a statement about the evidence available to you, not
about the content's honesty. It must not count toward the BS score the way a 🟠 does. Score on:

- ❌ **false** and 🟠 **misleading** — these are the content's failures, and they drive the number
- ✅ **confirmed** — pulls the number down
- 🟡 **plausible** — nearly neutral. Weight it by *why* it landed there: "hedged prediction" is mildly
  against the content; "capped by a tier-4 ceiling" is not the content's fault at all

This matters more than it looks, because reputable sources are the ones most often unreachable — see
[experiments/](../../../experiments/2026-07-30-credible-sources.md). Without this rule the tool scores
content as more dishonest exactly when good sourcing is hardest to reach, which is a bias in the
instrument, not a finding about the world.

**When load-bearing claims went unverified, it matters why.**

- **Unreached** — you ran out of budget, the source was blocked, the page was down. **Do not score.**
  A number would imply work that wasn't done. Report what you found and say the thesis wasn't audited.
- **Unverifiable in principle** — private financials, undisclosed internal data, unnamed clients.
  **Score, and say what the score covers.** Here the unverifiability *is* the finding: content whose
  entire proof rests on numbers only the seller can see has told you something important about itself.
  Put a load-bearing warning next to the tally naming which claims are unauditable and why, and make
  clear the score covers the checkable perimeter, not the core.

The distinction is the whole point: "I couldn't check this" and "nobody outside this company could
ever check this" are different findings, and only one of them is about the content.

Anchor on verified claims first, adjust with signals:

- **0–2 Solid.** Factual claims check out; conclusions follow from evidence; incentives disclosed.
- **3–4 Mostly fine.** Minor exaggerations or unhedged predictions; core content survives verification.
- **5–6 Hype-heavy.** True facts arranged to mislead; success wildly overstated; key context missing.
- **7–8 Mostly bullshit.** Load-bearing claims false or unverifiable; content exists to funnel to a product.
- **9–10 Fabricated.** Demonstrably false core claims, fake proof, or scam mechanics.

## Report card template

```markdown
# BS Report: <title>

**Source:** [<title>](<url>) — <author>, <platform>, <date> · <views/engagement>
**Checked:** <fetch date> · bullshit-detector <version>
**BS score: N/10 — <one-line verdict>**

## What it says (neutral summary)
2–4 sentences. No judgment here.

## Load-bearing claims
The ones the thesis dies without. Verify all of them.

| # | Claim (with timestamp/location) | Type | Verdict | Evidence |
|---|--------------------------------|------|---------|----------|

## Incidental claims
Supporting detail. Wrong here is embarrassing, not fatal.

| # | Claim (with timestamp/location) | Type | Verdict | Evidence |
|---|--------------------------------|------|---------|----------|

In Evidence, name the source tier when it changes the verdict, and say so when evidence existed but
was unreachable.

**Every claim backed by more than one URL must open its Evidence cell with an origin count**, and
**the marker must be a link to the origin**:

```markdown
[4 URLs → 1 origin](https://example.org/the-filing)
```

Not optional, and not only when syndication is suspected — a reader cannot tell corroboration from
an echo unless the count is always there, and "no marker" must mean "single source", never "nobody
looked".

**A verdict a reader cannot click through to is asking for trust it hasn't earned.** Every row
carrying a verdict that came from a search must contain at least one working link — the origin
marker where there is one, the source itself where there isn't. Naming four outlets and linking
none tells the reader to go and redo your work, which is the work they came here to avoid. This is
the same rule as linking the source in the header, one level down, and it matters more: the header
proves what was judged, these prove the judging.

The exceptions are the rows where nothing was searched — `⚪ not checked`, and `❓ unverifiable by
construction` — plus rows whose basis is another row (a derived figure, an arithmetic check), which
should say which claim they rest on instead.

State what the origin *is* when it matters: `[8 URLs → 1 origin: vendor press release](url)` is the
whole story in six words. What this marker says is **"these URLs are not independent"** — nothing more. It
is not a fabrication signal. Syndicated reporting is usually accurate; it is simply one source
wearing many URLs, and this tool has no way to detect fabrication.

**Every claim carrying a verdict must have had its own search.** If verification was capped (see
SKILL.md step 4), the claims you did not individually check still belong in the table — but with
verdict `⚪ not checked` and an empty evidence cell, never a substantive verdict inherited from a
neighbouring search or from memory. Close with a tally that separates the two:

> **Tally: N claims extracted, M individually source-checked** — a confirmed, b plausible,
> c misleading, d false, e unverifiable. K claims were not checked; P were opinion or anecdote and
> are not rateable.
>
> **Ambiguous: J claims dropped before verification; K checked under every reading** — what the
> J were, in a few words, and which readings the K carried.

The second half is omitted when `K` is 0. `J` counts claims whose meaning could not be pinned down
at all; `K` counts claims that had more than one reading, were checked under all of them, and
reached the same verdict either way — those are ordinary table rows and **do** count toward `N`
(step 3). Reporting them together in one number would merge two different findings about the
content: nobody can tell what this means, versus this means two things and both are wrong.

`M` is the number a reader should judge the report by. A table of 20 verdicts built on 14 searches
overstates the work, and this tool cannot afford to overstate anything.

**The ambiguous line is required, and `0` is a real answer.** Step 3 drops claims whose meaning the
content never fixes, so `N` is a filtered number — and a filtered number that doesn't say it was
filtered reads as a complete inventory. Without the line a reader cannot tell a content with four
checkable claims from one with four checkable claims and eleven that could mean anything, which is
most of what they wanted to know. `J` is counted separately and is deliberately *not* part of `N`:
these claims were never rated, so folding them into the table would put unrated rows next to rated
ones and break the tally arithmetic. When `J` is high, say so in the bottom line — content that
can't be pinned down is a finding about the content, not a limitation of the check.

**Count the rows, then check the sum before you write the line.** Every verdict bucket plus the
unchecked, unverifiable, and not-rateable counts must add up to `N` exactly. Do not estimate the
tally from memory of what you wrote — go back through the table and count. A fact-checking report
whose own arithmetic doesn't reconcile discredits every number above it, and this is the single
easiest error for a reader to catch.

**`M` must be countable from the table too.** A reader who disagrees with your total needs to be able
to recount it, so ❓ rows must say which kind they are:

- *"searched; nothing found"* — a search ran, so it **counts toward `M`**. Name the gap that stopped
  you rather than leaving it at "nothing found": *"searched three angles; the underlying study was
  never located"* tells the reader what kind of hole this is, and tells a later run where to start
- *"unverifiable by construction — private financials / unnamed subject / no record can exist"* —
  nothing was searched, so it **does not count toward `M`**

Both are legitimate ❓ verdicts and the difference matters: one says the evidence is missing, the
other says the claim was built so that no evidence could ever exist. Never assert a summary number
the table doesn't support — that is the same failure as an unsourced verdict, one level up.

**The two header fields are not decoration.**

- **Link the source.** A reader must be able to open the thing being judged and check the call
  themselves. A fact-check that can't be traced back to its subject is asking for trust it hasn't
  earned. If the content has no stable permalink (a paste, a local file, a deleted post, a draft
  you were asked to check), say so **in the Source line, in those words** — `no permalink` or
  `no stable URL`, plus the reason — rather than linking something approximate. An invented link
  is worse than an absent one, and the validator accepts the declaration but not silence.
- **Stamp the version.** Verdicts move between releases — the rubric, the source hierarchy and the
  verdict rules all change — so a report without a version can't be reproduced or fairly compared.
  Read it from `.claude-plugin/plugin.json` and print it as-is. If the skills were installed without
  a manifest and no version is available, write `version unknown` rather than guessing.

Both fields also protect the reader from search non-determinism: the same claim re-checked a week
later can surface a different evidence base, so a report is a dated reading, not a permanent verdict.

## Hype signals observed
Bulleted, each with a quoted example from the content.

## Incentive analysis
Who benefits if you believe this, and how.

## Bottom line
3–5 sentences: what's actually true, what's noise, what a viewer
should take away. If some advice is genuinely sound, say which.
If the claims check out but the conclusion still doesn't follow
from them, say that here — the table above cannot show it.

## What a hostile reader would hit first
Ranked, 3–5 items. The errors an opponent leads with are not the
same as the ones that matter most to the argument: a checkable
date error in the opening act does more damage than a subtle
misattribution buried at the end. Name each one, say why it lands,
and — where it's fixable — say what would fix it.

*run: 16m55s, searches 24, tools 30, coverage 1, per claim 44s*
```

### The run line

One italic line, last thing in the report, and deliberately dull. A reader came to find out
whether the content is true, not what it cost to find out — so this stays a footnote, and
anything longer belongs in the run record beside the file rather than in the report.

It earns its place by being checkable. `per claim` is the wall time over `M`, not a fresh
number, so it cannot drift from the tally. And `searches` against `tools` is a reconciliation
a reader can do at a glance: **every search is at least one tool call, so searches can never
exceed tools.** A report claiming 31 searches from 15 tool calls is claiming work it did not
do, and that is now visible on the face of it rather than buried in a transcript nobody reads.

`coverage` counts `coverage-check` runs — the expensive call, and the one worth watching.
It is spelled out rather than shortened to `checks`, because a report that already says
"individually source-checked" and carries a `⚪ not checked` verdict cannot afford a third,
different meaning of the same word.
