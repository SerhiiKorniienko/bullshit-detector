# BS Report: How to Get So Rich as a Dev It Feels Illegal

**Source:** [How to Get So Rich as a Dev It Feels Illegal](https://youtu.be/CEqosMn3m34) — Bgo, YouTube, published 2026-07-20 · 18,610 views · 835 likes · 44.5K subscribers
**Checked:** 2026-07-31 · bullshit-detector v0.7.0
**BS score: 7/10 — the advice underneath is ordinary and mostly fine; every number offered as proof of it is either the seller's own or inflated, and the video ends in a funnel.**

## What it says (neutral summary)

A software engineer who says he now runs his own consultancy argues that devs stay poor because
they sell hours instead of owning leverage. Three levers: the code itself, other people's problems
(value-priced automation), and distribution/brand. He adds that communication — translating code
into money for CEOs — is what actually gets paid, and that speed beats preparation, citing Amazon's
"Bias for Action" and his own decision to quit the day ChatGPT launched. The video closes with a
free live training that feeds his paid accelerator, Code to CEO.

## Load-bearing claims

| # | Claim (with timestamp/location) | Type | Verdict | Evidence |
|---|--------------------------------|------|---------|----------|
| 1 | [00:00] "Last year my company made three times more than the combined salaries of an L7 Google, a Meta, and an Amazon engineer" [i.e. 2025 revenue of his consultancy] | factual | ❓ unverifiable by construction — private company revenue, no filing exists | Size of the implied number, for scale: median total comp is [$1.04M Google L7](https://www.levels.fyi/companies/google/salaries/software-engineer/levels/l7/locations/united-states), $1.18M Meta E7, $634K Amazon L7 → ~$2.85M combined, so 3× ≈ $8.5M. On a "salaries = base pay only" reading (~$815K combined) it is ~$2.4M. His own program page separately advertises "$450K+/month" (~$5.4M/yr) and his bio page "hit 7 figures in ARR" — three self-reported figures that only reconcile if you pick the right reading of each |
| 2 | [00:00, 01:05] "My firm was billing me out at $1,850 an hour to three different clients while I was getting less than $150 an hour" | factual | ❓ searched; the firm is unnamed, so unfalsifiable — and no published rate card comes near it | [2 URLs → 2 origins: GSA contract-rate guidance + a 2026 consulting rate survey](https://fed-spend.com/blog/government-contract-labor-rates-gsa-schedule-2026): fully burdened federal IT rates in 2026 top out around $340/hr for senior SMEs; commercial dev consultancies run [$150–400/hr, with elite firms to ~$900](https://www.raftlabs.com/blog/software-development-consulting-rates). $1,850/hr for a staff engineer's hour is 2–5× the top of the reachable ranges. Tier 3–4 sources; the specific firm can't be identified |
| 3 | [02:06] "That's almost $6,000 an hour that was coming in off my keyboard" [one hour of his work billed simultaneously to three clients at $1,850 each] | factual | 🟠 misleading | Billing one hour at full rate to more than one client is [double billing](https://www.americanbar.org/groups/law_practice/resources/law-technology-today/2023/what-lawyers-need-to-know-about-double-billing/) — prohibited under ABA Model Rule 1.5 absent disclosure and consent, and treated as fraud-adjacent across professional services. The generous reading is that he worked on three clients' projects across three separate hours, which is normal — and which deletes the "$6,000 an hour" figure the whole leverage argument opens with |
| 4 | [03:09] "Two employees spending 15 hours a week copying data between two systems by hand comes out to roughly 60 grand a year in payroll" | factual | 🟠 misleading | [3 URLs → 3 origins: BLS OEWS, ZipRecruiter, Indeed](https://www.bls.gov/oes/2023/may/oes439021.htm) — BLS puts data entry keyers at a $19.29 mean hourly wage ($40,130/yr, May 2023); the aggregators land at $19.47–19.70. 15 h/wk = 780 h/yr → ~$15K. Read as 15 h/wk *each* (1,560 h) → ~$30K. $60K needs ~$77/hr for data entry, or ~$38/hr fully loaded across two people — 2–4× over the wage data either way |
| 5 | [03:09] "You automate this in about 3 weeks, charge them $15,000 — to you that's maybe a day of actual coding" and they save $60K/yr forever | factual | 🟠 misleading | Rests on claim 4: the ROI pitch is 4:1 in year one only because the cost being replaced is inflated 2–4×. At BLS wages the same job saves ~$15K/yr, i.e. the fee equals a year of the savings. "Forever" also assumes zero maintenance on an integration built in a day, which the same video concedes elsewhere ("a little bit of maintenance work involved") |
| 6 | [13:39] "The average founder inside Code to CEO lands their first client in about 47 days" | factual | ❓ searched; the only source is the seller's own landing page | [codetoceo.com](https://www.codetoceo.com/) prints "47 Days" average time to first client alongside "$15K+ average first deal", "31+ developers have quit their 9-5" and "$5.3M+ total partner revenue" — tier 4, self-reported, no denominator, no independent audit, and the same page says acceptance is "roughly 1 in 45 applicants", so the average describes a filtered cohort |
| 7 | [12:36] "A year later from that date I was already making over six figures a month" | factual | ❓ unverifiable by construction — private income, no record can exist | Corroborated only by his own properties, which give different numbers for the same business (see claim 1) |
| 8 | [02:06] "When you're an employee, you are always on the adding side of that equation. It is a linear relationship because that is literally the deal that you signed" | factual | 🟠 misleading | At the exact levels the video's opening line invokes, employee pay is mostly equity, not hours: [Meta E7 median $1.18M = $330K base + $790K/yr stock + $57K bonus](https://www.levels.fyi/companies/meta/salaries/software-engineer/levels/e7/locations/united-states). Stock is an owned, compounding asset — the "multiplying" side of his own metaphor. The linear-vs-leveraged split is real for hourly contractors, not for the senior employees he benchmarks against |
| 9 | [11:32] "Amazon has 16 leadership principles. Do you know which one they grill you the hardest on in interviews? The bias for action" | factual | 🟠 misleading | [3 URLs → 3 origins: Amazon's careers site, Amazon's own interview guidance, interviewing.io](https://www.aboutamazon.com/news/workplace/amazon-leadership-principles-interview) — Amazon states "all Leadership Principles are equally important" and ranks none; interviewing.io tells candidates to treat Customer Obsession as the overarching theme and to "ignore the urge to guess which specific LP a question is asking about". Bias for Action is real and commonly tested; the ranking asserted around it has no source. Searched four angles; no public frequency data on LP questions exists |
| 10 | [11:32] "Amazon has 16 leadership principles" | factual | ✅ confirmed | [amazon.jobs](https://www.amazon.jobs/content/en/our-workplace/leadership-principles) lists exactly 16, Bias for Action ninth (tier 1, the company's own canonical list) |
| 11 | [13:39] "Speed is literally a money multiplier and the 47 days average proves it" | factual | 🟠 misleading | Rests on claim 6. A mean time-to-first-client among accepted, paying members of a 1-in-45 program has no comparison group and no failure data — it cannot separate speed from selection, prior network, or the ones who never landed a client at all. The number, even taken at face value, proves nothing about causation |
| 12 | [07:21] The same project described two ways: "one sentence gets you $150 an hour, whereas the other one gets you that 1850 per hour" | factual | 🟠 misleading | Rests on claim 2, and contradicts his own account 90 seconds earlier: at [05:15] the $1,850 exists because "the client trusted their name over mine" — brand and client ownership, not phrasing. The video attributes a 12× rate gap to a sentence in one section and to distribution in the other |

## Incidental claims

| # | Claim (with timestamp/location) | Type | Verdict | Evidence |
|---|--------------------------------|------|---------|----------|
| 13 | [01:05] As an employee "past 40 hours, I stop getting paid, right? I don't get paid overtime" | factual | ✅ confirmed | [DOL Fact Sheet #17E](https://www.dol.gov/agencies/whd/fact-sheets/17e-overtime-computer): FLSA §13(a)(1) and §13(a)(17) exempt software engineers and similar computer employees from overtime when paid on a salary basis at the standard level or ≥$27.63/hr (tier 1) |
| 14 | [04:13] "Dom, inside Code to CEO, has done this kind of deal time and time again, back when he was in the US with Port City AI, and now in Sydney, Australia, doing the same exact thing" | factual | ✅ confirmed | [3 URLs → 3 origins: Alabama's AI vendor registry, Portcity AI's own site, his personal site](https://aitaskforce.alabama.gov/ai-vendor-list/portcity-ai-llc/) — Dominik Fretz founded Portcity AI LLC (listed as an Alabama state AI vendor, serving Birmingham/Lower Alabama), and now runs Harbour Edge Intelligence from [Sydney/Townsville, Australia](https://dominikfretz.com/). The one named third party in the video checks out in detail |
| 15 | [14:40] "On July 26th, 11:00 a.m. Pacific Standard Time, I'm hosting a live training showing you how to land your first $10,000 plus client as a developer without writing a single line of production code… completely for free" | factual | 🟡 plausible | A free live masterclass funnel exists at [workshop.codetoceo.com](https://workshop.codetoceo.com/), same 11:00 PST slot — but it is now dated Sunday 30 August 2026 and the topic reads "how to go from zero to a SaaS that people actually pay for", with the FAQ saying "if it resonates and you want to go deeper, Code to CEO exists for that". A rotating-date evergreen webinar into a paid accelerator; the specific 26 July instance can't be confirmed after the fact |
| 16 | [10:29] Code to CEO members close deals worldwide — "Pedro from Brazil, closing deals in Portuguese", "Toufic from Bangalore", "Marco from Serbia", "Carl from Switzerland" | factual | ❓ searched; first names only, no identifiable subjects | Searched the names against the [program](https://www.codetoceo.com/) and generally; the searches returned unrelated people. Unlike Dom (claim 14), these are unfalsifiable as named — a first name and a country is not a checkable referent |
| 17 | [12:36] "The day Chat GPT launched… that is very same day, I put in my two weeks' notice and I started working on my consultancy" | anecdote | — | The date anchor is real — [ChatGPT launched 30 November 2022](https://en.wikipedia.org/wiki/ChatGPT) — but his resignation leaves no public record. Note the era detail: "the doom threads were flying on Reddit and on X" — the platform was still called Twitter until July 2023 |
| 18 | [12:36] "I had $258 in my bank account and a rent coming in" | anecdote | — | Repeated verbatim on his own bio page ("Down to my last $258") — consistent, self-sourced, and unverifiable |
| 19 | [06:17] The highest-paid person at his old firm was a partner who had no engineering degree and "wasn't even in the top 10" engineers | anecdote | — | Unnamed firm, unnamed person |
| 20 | [10:29] "English was my third language, and had a very heavy accent" | anecdote | — | Consistent with his bio page (immigrated from Armenia at 12); nothing to check |
| 21 | [13:39] "Nobody tells you this about business… there is no course. The market is the course" | opinion | — | Followed 60 seconds later by a pitch for his course-shaped free training and accelerator |
| 22 | [09:26] "When the risk for them hits zero, the price stops being the conversation, and you can charge however much you want easily" | opinion | — | Absolute framing, no failure case, no mention of clients who say no |
| 23 | [14:40] "How to land your first $10,000 plus client as a developer without writing a single line of production code" | prediction | — | Unhedged outcome promise with no stated failure rate, timeline or competition |

> **Tally: 23 claims extracted, 14 individually source-checked** — 3 confirmed, 1 plausible, 7 misleading. 5 unverifiable; 7 not rateable.
>
> **Ambiguous: 0 claims dropped before verification** — two claims carry unresolved readings
> (claim 1: "salaries" as base pay or total comp; claim 4: 15 h/wk total or per employee) and were
> checked under both readings, which reach the same verdict either way.
>
> **Load-bearing warning:** the video's entire evidentiary base — his revenue, his monthly income,
> his old firm's bill rate, his program's 47-day average — is unverifiable in principle. No outsider
> can audit any of it. The score covers the checkable perimeter, not the core.

## Hype signals observed

- **Funnels to a paid product.** The video is a 15-minute lead magnet: free training → application
  → strategy call → paid accelerator. "The link will be in the description below. It's going to be
  completely for free."
- **Anecdote (n=1) presented as a repeatable system.** One person's outcome, then "this has been the
  same exact case with every other founder inside Code to CEO."
- **Social proof substituting for evidence.** "Pedro from Brazil", "Toufic from Bangalore",
  "Marco from Serbia" — countries and first names, no checkable subject.
- **Unrealistic specificity where checkability is lowest.** "$1,850 an hour", "47 days", "$258",
  "over six figures a month" — precision rises exactly where nobody can verify it.
- **Success attributed entirely to the method, never to timing or audience.** Quitting into the
  post-ChatGPT AI-consulting boom with a YouTube channel behind him is the "bias for action" story;
  the market timing and the distribution he already had are not mentioned as factors.
- **Self-refuting absolute.** "There is no course. The market is the course" — 60 seconds before
  the course pitch.
- **No failure rates.** 31+ developers quit their jobs; how many joined, how many didn't land a
  client, and how many lost money is not stated anywhere in the video or on the program page.

## Incentive analysis

Bgo sells Code to CEO, a 180-day accelerator for engineers going independent, gated by application
and a strategy call, price undisclosed publicly. Every claim in the video raises the perceived value
of that program: the $1,850/hr story establishes that employers capture your value, the $60K payroll
figure establishes that clients will pay handsomely for a day's work, the 47-day average establishes
that his members get there fast. He profits from you believing these regardless of whether they are
true — and each one is either his own private number or an estimate that runs 2–4× over the public
data. The one claim he made that involves an independently checkable third party (Dom / Port City AI)
turned out to be accurate, which is worth saying plainly.

## Bottom line

The underlying advice is unremarkable and largely sound: price on value rather than hours, learn to
state technical work in money terms, build distribution, start before you feel ready. None of that
is bullshit, and a mid-level engineer could act on it profitably. What doesn't survive is the
evidence offered for it. Every proof number is either self-reported and unauditable (his revenue,
his monthly income, the 47-day average) or inflated against public data (the $60K payroll figure is
2–4× BLS wages; $1,850/hr is 2–5× any published rate card). Two arguments also fail on their own
terms even if you grant the numbers: "almost $6,000 an hour off my keyboard" only works if one hour
was billed three times, which is a thing professional-services rules prohibit rather than a thing to
envy; and a 47-day average among the 1-in-45 who were accepted and paid cannot show that speed
causes money. Treat it as a competent sales letter for a coaching program that happens to contain
real advice — not as evidence that the program works.

## What a hostile reader would hit first

1. **The $60,000 payroll figure** [03:09]. It's the only fully checkable number in the business case
   and it's off by 2–4×; BLS puts data entry at ~$19/hr, so 15 h/wk is ~$15K/yr, not $60K. Fix:
   state the wage assumption out loud, or use a realistic $15–30K saving — the value-pricing argument
   still works at 1:1 ROI, it just sounds less magical.
2. **"$6,000 an hour off my keyboard"** [02:06]. Billing the same hour to three clients is a rules
   violation in every professional-services field that has rules, so the story either describes
   misconduct or describes three separate hours. Fix: say "three clients, three hours" and drop the
   $6,000 figure.
3. **"There is no course. The market is the course"** [13:39], sixty seconds before the course pitch.
   It reads as a rhetorical tic he didn't check, and it's the line that will get quoted in the
   comments. Fix: cut it, or own the tension.
4. **The Amazon ranking** [11:32]. Amazon says all 16 principles are equally weighted and the
   interview-prep world points at Customer Obsession; "the one they grill you the hardest on" is
   asserted with no basis. The principle count is right, which makes the invented ranking sit oddly
   next to it. Fix: "one they test heavily" is defensible; "the hardest" is not.
5. **Opening with a number nobody can check** [00:00]. "3× the combined salaries of an L7 Google, a
   Meta, and an Amazon engineer" implies roughly $8.5M on the natural reading, against $450K/month
   on his own site and "7 figures in ARR" on his bio page. A hostile reader who opens two tabs finds
   three different numbers for one business. Fix: pick one figure, define it (revenue? profit? ARR?),
   and use it everywhere.

*run: 11m31s, searches 21, tools 45, coverage 0, per claim 49s*
