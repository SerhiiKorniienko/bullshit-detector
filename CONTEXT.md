# Bullshit Detector

A collection of portable agent skills that fetch any content source and analyze it — fact-checking, summarizing, explaining.

## Language

**Source**:
Anything a user can point the skills at — a YouTube video, article URL, tweet, PDF, or local file.

**Adapter**:
The per-source code path inside `fetch.py` that turns one Source type into normalized text. Adding a platform = adding an Adapter.
_Avoid_: fetcher, scraper, integration

**Normalized text**:
What every Adapter emits: clean text with location markers (`[mm:ss]` timestamps or `[p.N]` pages) plus YAML front-matter **Metadata**.

**Metadata**:
The front-matter block on Normalized text — title, author, date, views/likes/followers, word count. Feeds the Incentive analysis and Hype signals.

**Claim**:
A single distinct assertion extracted from content, classified as `factual`, `prediction`, `opinion`, or `anecdote`. Only factual Claims get web-verified.

**Verdict**:
The rating a verified Claim receives: ✅ confirmed / 🟡 plausible / 🟠 misleading / ❌ false / ❓ unverifiable. Verdicts require sources — never assigned from model memory.

**Hype signal**:
A rhetorical pattern that correlates with bullshit (urgency, absolutes, n=1 anecdotes as systems, funnels). A signal, not proof — counted and quoted, never treated as a verdict.

**BS score**:
The 0–10 rating anchoring the report card. Driven primarily by Verdicts, adjusted by Hype signals. 0–2 solid, 5–6 hype-heavy, 9–10 fabricated.

**Report card**:
The detector's output document: neutral summary, Claims table with Verdicts and evidence, Hype signals observed, Incentive analysis, bottom line with the BS score.

**Incentive analysis**:
The report-card section answering "who benefits if you believe this, and how" — funnels, products sold, conflicts of interest.

**Promoted bucket**:
A `skills/` folder (`analysis/`, `ingestion/`) whose skills ship in the plugin and appear in the top-level README. `in-progress/` is not promoted.

## Relationships

- An **Adapter** turns one **Source** type into **Normalized text** + **Metadata**
- The detector extracts **Claims** from Normalized text; factual Claims receive **Verdicts**
- **Verdicts** + **Hype signals** + **Metadata** drive the **BS score** on the **Report card**
- Analysis skills consume Normalized text only — they never touch **Sources** directly
