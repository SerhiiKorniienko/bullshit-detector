# Bullshit Detector

[![skills.sh](https://skills.sh/b/SerhiiKorniienko/bullshit-detector)](https://skills.sh/SerhiiKorniienko/bullshit-detector)

Agent skills that fact-check the internet. Point your agent at a viral YouTube video, article, tweet, or PDF — get a claim-by-claim verification report with sources and a **BS score (0–10)** instead of taking "10 WAYS TO MAKE MONEY WITH AI 🤯" at face value.

Portable [Agent Skills](https://agentskills.io) — plain markdown + self-contained Python. They work in Claude Code, Codex, OpenCode, and any harness that supports the skills format and has web search.

Built in the open with [Claude Code](https://claude.com/claude-code) — an AI helped build the tool that fact-checks AI hype, and the [example report](./examples/report-14-ways-to-make-money-with-ai.md) is it auditing its own kind.

Follow [@SerhiiFounder](https://x.com/SerhiiFounder) for new skills and fact-check experiments, or [join the newsletter](https://korniienko.dev/newsletter) to get them in your inbox.

## Quickstart (30-second setup)

1. Install [uv](https://docs.astral.sh/uv/) if you don't have it (the fetch script uses it to self-resolve its dependencies).

2. Run the skills.sh installer and pick the skills and agents you want:

```bash
npx skills@latest add SerhiiKorniienko/bullshit-detector
```

3. Ask your agent: *"is this bullshit? \<url\>"*, *"fact-check this video"*, *"summarize \<url\>"*, *"explain the part at 12:30"*.

## Install as a Claude Code plugin

Prefer a managed bundle that updates when a new version ships, instead of copied files you maintain yourself? Inside Claude Code:

```
/plugin marketplace add SerhiiKorniienko/bullshit-detector
/plugin install bullshit-detector@serhii-korniienko
```

Two ways to install, two philosophies:

- **[skills.sh](https://skills.sh/SerhiiKorniienko/bullshit-detector)** copies the skills into your setup so you can hack on them and make them your own. Works with any agent (Claude Code, Codex, OpenCode, …).
- **The plugin** keeps them as a read-only, always-current bundle — best when you just want it to work and follow along as it evolves. Claude Code only.

**Pick one, not both** — installing both gives Claude Code two copies of every skill.

## Why These Skills Exist

### #1: Viral ≠ true

A finance guy with 1M views tells you the "only 14 ways to make money with AI". How much of it is real? Views, production value, and confidence are not evidence. The fix is boring: extract every claim, check each against independent sources, and score what survives. That's exactly the work agents with web search are good at and humans never bother doing.

**The fix:** [`bullshit-detector`](./skills/analysis/bullshit-detector/SKILL.md) — per-claim verdicts (✅ confirmed / 🟡 plausible / 🟠 misleading / ❌ false / ❓ unverifiable), a hype-signal scan, an incentive analysis ("who benefits if you believe this"), and a 0–10 BS score. Verdicts require sources — the skill forbids confirming or refuting from model memory alone.

### #2: Agents can't watch videos

Your agent can't sit through a 27-minute video, and YouTube's official API won't give you captions for videos you don't own. Same story with tweets ($100/mo API) and paywalled articles.

**The fix:** [`fetch-content`](./skills/ingestion/fetch-content/SKILL.md) — one script that turns any URL into clean text + metadata with no API keys: YouTube transcripts via yt-dlp, articles via readability extraction, PDFs, tweets via free endpoints. Every failure mode produces an actionable hint (paywall → paste, no captions → Whisper) instead of a silent guess.

### #3: Separation of fetching and judging

Ingestion and analysis are different jobs. Scripts do the deterministic work (fetch, parse, normalize); the agent does the reasoning (extract claims, search, judge). Because analysis skills only ever see normalized text + metadata, adding TikTok support one day touches zero analysis logic — and the same detector works on a tweet and a 3-hour podcast.

## Example

A real run against a 1.16M-view "make money with AI" video: **[examples/report-14-ways-to-make-money-with-ai.md](./examples/report-14-ways-to-make-money-with-ai.md)**.

> **BS score: 5/10 — real tools, real trends, guru math, and a funnel every four minutes.**
> 12 claims verified: 4 confirmed, 2 plausible, 3 misleading, 0 false, 3 unverifiable. Among the catches: "Renaissance, D.E. Shaw, Two Sigma only trade employees' money" (true for one fund of one firm), and marketplace stats sourced from the marketplace's own PR.

## Reference

All skills are **model-invoked**: you can call them explicitly, and the agent also reaches for them when your request fits ("is this legit?" triggers the detector).

### [Analysis](./skills/analysis/README.md)

Reason about content. Source-agnostic — they never care where the text came from.

- **[bullshit-detector](./skills/analysis/bullshit-detector/SKILL.md)** — Extract every claim, verify each against independent sources via web search, scan for hype signals, produce a report card with per-claim verdicts and a 0–10 BS score.
- **[summarize](./skills/analysis/summarize/SKILL.md)** — Structured TLDR with timestamped key points, notable quotes, and an honest "worth your time?" call.
- **[explain](./skills/analysis/explain/SKILL.md)** — ELI5 → deep-dive explanation of the content or any concept in it, with a jargon glossary and the prerequisites the original assumes.

### [Ingestion](./skills/ingestion/README.md)

Turn any source into clean text + metadata.

- **[fetch-content](./skills/ingestion/fetch-content/SKILL.md)** — YouTube transcripts, articles, PDFs, tweets, local files. One script, auto-detects source, no API keys.

## Roadmap

See [skills/in-progress](./skills/in-progress/README.md): `compare` (same topic across sources — who's right?), `transcribe` (Whisper for TikTok/Reels and caption-less videos), X thread walking.

## Stay in touch

I'm building these skills in the open — new detectors, adapters, and real fact-check reports as they land.

- Follow [@SerhiiFounder](https://x.com/SerhiiFounder) on X
- [Join the newsletter](https://korniienko.dev/newsletter) — a short weekly-ish email, no spam, unsubscribe anytime

## License

MIT
