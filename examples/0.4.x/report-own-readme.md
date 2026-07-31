# BS Report: this repository's own README

**Source:** `README.md` @ [SerhiiKorniienko/bullshit-detector](https://github.com/SerhiiKorniienko/bullshit-detector), v0.4.1 · checked 2026-07-29
**BS score: 3/10 — the technical claims hold up; the friction is undersold and one price is two years stale.**

*Requested on Hacker News: "Can someone please use this skill against the claims in its own repo?" Published unedited, including the parts that don't flatter it.*

## What it says (neutral summary)

The README pitches a set of portable Agent Skills that fact-check content: point an agent at a YouTube video, TikTok, article, tweet, or PDF and get a claim-by-claim verification report with sources and a 0–10 BS score. It argues three motivations — viral content isn't checked, agents can't watch videos and official APIs won't hand over the text, and fetching should be separated from judging. It offers two install paths (skills.sh installer, Claude Code plugin), links two example reports, and funnels readers to the author's X account and newsletter.

## Claims

| # | Claim (location) | Type | Verdict | Evidence |
|---|---|---|---|---|
| 1 | Skills "work in Claude Code, Codex, OpenCode, and any harness that supports the skills format and has web search" (intro) | factual | ✅ confirmed | Codex reads `SKILL.md` from `.codex/skills/` and `~/.agents/skills/` ([Serenities AI](https://serenitiesai.com/articles/agent-skills-guide-2026), [rzlt.io](https://www.rzlt.io/blog/the-ultimate-openai-codex-skills-directory---2026)); OpenCode has first-party skill discovery reading `~/.claude/skills/` and `~/.agents/skills/` ([OpenCode docs](https://opencode.ai/docs/skills/)) |
| 2 | "Built in the open with Claude Code" (intro) | factual | ✅ confirmed | 4 of 6 commits carry `Co-Authored-By: Claude` trailers (`git log`) |
| 3 | "YouTube's official API won't give you captions for videos you don't own" (Why #2) | factual | ✅ confirmed | `captions.download` requires OAuth 2.0 and edit permission on the video; the API does not permit downloading captions for videos not belonging to the authenticated user ([Google for Developers](https://developers.google.com/youtube/v3/docs/captions/download), [implementation guide](https://developers.google.com/youtube/v3/guides/implementation/captions)) |
| 4 | "Same story with tweets ($100/mo API)" (Why #2) | factual | 🟠 misleading | Stale by two years and two pricing regimes. Basic launched at $100/mo in 2023, was repriced to $200/mo, and on 2026-02-06 X made pay-per-use the default with no Basic signup for new developers ([Postproxy](https://postproxy.dev/blog/x-api-pricing-2026/), [Blotato](https://www.blotato.com/blog/twitter-api-pricing)). The argument survives — the official API is still not viable here — but the number is wrong |
| 5 | "no API keys" anywhere in the fetch path (Why #2) | factual | ✅ confirmed | No `api_key`, `token`, `Bearer`, or `os.getenv` anywhere in `skills/ingestion/fetch-content/scripts/fetch.py` |
| 6 | "Every failure mode produces an actionable hint (paywall → paste, no captions → Whisper) instead of a silent guess" (Why #2) | factual | ✅ confirmed | `fail(msg, hint)` at `fetch.py:44`; hints at lines 178, 263–264, 330, 385, 391–392 cover exactly the paywall and missing-caption cases named |
| 7 | "adding TikTok support one day touches zero analysis logic" (Why #3) | factual | 🟡 plausible | The design holds — nothing in the TikTok adapter requires an analysis change. But the commit that actually added TikTok (`4936845`) also modified `skills/analysis/bullshit-detector/SKILL.md`. Those edits were unrelated features bundled into one commit, so the claim isn't refuted; the repo just never demonstrates it cleanly |
| 8 | Dan Martell report: 1.16M views, 5/10, "12 claims verified: 4 confirmed, 2 plausible, 3 misleading, 0 false, 3 unverifiable" (Example) | factual | ✅ confirmed | Matches `examples/0.4.x/report-14-ways-to-make-money-with-ai.md` exactly, including the precise view count of 1,164,773 |
| 9 | Second-sun report: 552K views, 9/10 (Example) | factual | ✅ confirmed | Matches `examples/0.4.x/report-second-sun-binary-star.md` |
| 10 | "Quickstart (30-second setup)" (heading) | factual | 🟠 misleading | Step 1 of the three-step quickstart is "Install uv if you don't have it." For anyone without uv, the claim is false by an order of magnitude. A commenter on the launch thread put it as "that's too much effort" |
| 11 | "Most TikToks ship with creator or auto-generated captions" (TikTok) | factual | ❓ unverifiable | No source, and no published figure for caption prevalence on TikTok could be found. Presented as fact; it's an impression from a small number of tests |
| 12 | "mlx-whisper on Apple Silicon, no system ffmpeg needed — PyAV decodes the audio" (TikTok) | factual | ✅ confirmed | PyAV has shipped binary wheels with FFmpeg libraries bundled since release 8.0.0, so no system FFmpeg is required ([PyAV docs](https://pyav.org/docs/develop/overview/installation.html), [pyav-ffmpeg](https://github.com/PyAV-Org/pyav-ffmpeg)) |
| 13 | "Use whisper-large-v3-turbo — smaller models garble words badly enough to break claim extraction" (TikTok) | anecdote | ❓ unverifiable | One internal comparison on one video. No benchmark, no WER figures, no published comparison. Plausible and consistent with model-size expectations, but it's an anecdote stated as a rule |
| 14 | "installing both gives Claude Code two copies of every skill" (Install) | factual | 🟡 plausible | Consistent with how skill directories and plugin bundles are both discovered, but not independently documented anywhere |
| 15 | "All skills are model-invoked… the agent also reaches for them when your request fits" (Reference) | factual | ✅ confirmed | This is the defining behaviour of the Agent Skills format: the agent reads the description, decides relevance, and loads the body on demand ([Termdock](https://www.termdock.com/blog/agent-skills-guide)) |
| 16 | Newsletter is "a short weekly-ish email" (Stay in touch) | prediction | ❓ unverifiable | Forward promise with no track record: zero issues have been sent as of this check |

**Tally: 16 claims — 9 confirmed, 2 plausible, 2 misleading, 0 false, 3 unverifiable.**

## Hype signals observed

- **Understated friction.** "Quickstart (30-second setup)" whose first step is installing a package manager. The honest number is "30 seconds if you already have uv."
- **Sources that trace back to the speaker.** The only evidence the tool works is two reports the author generated with the tool, about content the author chose. No independent evaluation, no eval harness, no third-party run. This is the standard "the only proof is my own material" pattern, and it applies here in full.
- **Grandiose framing.** "Agent skills that fact-check the internet" and "Fact-check the internet" as a banner line, for something that processes one URL at a time.
- **Rhetorical strawman.** "instead of taking '10 WAYS TO MAKE MONEY WITH AI 🤯' at face value" — sets up the dumbest possible alternative to compare against.
- **Social proof furniture.** A skills.sh badge is the first element on the page, above any description of what the thing does.
- **Stale specifics presented as current.** The "$100/mo API" figure reads as a checked fact and hasn't been true since 2023.

Not observed, and worth stating: no urgency or scarcity language, no income or outcome claims, no paid product, no unverifiable credentials, no dismissal of skeptics. The limitations are stated in several places rather than hidden.

## Incentive analysis

Nothing is for sale. The code is MIT, there's no hosted service, no signup, no key, and no paid tier. The funnel is attention: an X follow and a newsletter subscription, both disclosed in the intro and repeated in the footer.

The real conflict is subtler and structural. The README's evidence that the detector works consists entirely of reports the detector produced, selected and published by its author. A reader who finds the reports persuasive concludes the tool is good; the tool's credibility and the author's are the same asset. The README doesn't hide this — it says outright there's no eval harness and that it can't say how often it's wrong — but the circularity is load-bearing and no disclosure removes it.

## Bottom line

The checkable technical claims hold. The portability claim is real (Codex and OpenCode both read the skill format), the YouTube API restriction is real, there are genuinely no API keys, the error hints exist exactly where the README says, PyAV really does remove the FFmpeg dependency, and both example reports' numbers match their source files to the digit — including a view count quoted as 1.16M that is actually 1,164,773.

What drags it to 3/10 is a repeated pattern of the friction being lighter in the README than in reality: a "30-second setup" that starts with installing a package manager, an API price two repricings out of date, "most TikToks have captions" asserted without a number, and a whisper model recommendation generalised from one test. None of these are false in spirit and none change whether the tool works. They're the same failure this tool flags in other people's content — a checkable detail stated one notch more confidently than the evidence supports — which is a fair thing to have caught on itself.

The honest summary for a reader: the thing does what it says, the setup is longer than advertised, and the only evidence it's accurate is evidence it produced about itself.
