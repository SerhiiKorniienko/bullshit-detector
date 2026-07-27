---
name: share
description: Turn a BS report (or any analysis result) into ready-to-paste posts for X/Twitter, LinkedIn, Facebook, Reddit, Hacker News, or a newsletter issue — plus a branded image carousel (PNGs + PDF) for visual platforms. Use when the user wants to share, post, publish, or promote a report, asks for "a thread", "a LinkedIn post", "a carousel", or "format this for X".
---

# share

Take a finished report and produce platform-native content, ready to paste. Nothing generic: each platform gets its own format, length, and link etiquette.

## Workflow

1. **Locate the report.** A file the user points at, the report from this conversation, or — if there is none — offer to run the `bullshit-detector` skill first.
2. **Ask which platforms** if not stated. Default set: X thread + LinkedIn post.
3. **Write the posts** following the per-platform specs in [PLATFORMS.md](PLATFORMS.md) exactly — hooks, length limits, link placement. Output each as a separate fenced block the user can copy verbatim.
4. **Carousel (if requested or if the platform benefits):** extract the report into a `slides.json` (schema below) and render:

```bash
uv run <this-skill-dir>/scripts/render_carousel.py slides.json -o carousel/
```

First run needs a one-time browser install: `uv run --with playwright playwright install chromium`. Output: `slide-N.png` (1080×1350, works on X, LinkedIn, Instagram) + `carousel.pdf` (LinkedIn document post).

## slides.json schema

```json
{
  "title": "Video/article title",
  "source": "Author · Platform · 1.16M views",
  "score": 5,
  "verdict_line": "Real tools, fantasy income math",
  "footer": "@SerhiiFounder · korniienko.dev/newsletter",
  "slides": [
    { "type": "hook" },
    { "type": "claim", "n": "1/12", "claim": "Quoted or paraphrased claim, ≤200 chars",
      "verdict": "misleading", "evidence": "One-sentence reality, ≤160 chars" },
    { "type": "cta", "headline": "Run it on anything",
      "lines": ["npx skills add SerhiiKorniienko/bullshit-detector", "korniienko.dev/newsletter"] }
  ]
}
```

Verdicts: `confirmed` / `plausible` / `misleading` / `false` / `unverifiable`. Pick 3–4 claim slides — the spiciest verdicts with the strongest evidence, not the first four. Hook and CTA slides bookend them.

## Rules

- **The report is the content; the tool is the footnote.** Hooks lead with findings ("12 claims, 3 misleading"), never with "I built a tool".
- Numbers must match the report exactly — a fact-checking brand cannot round its own stats.
- Stay honest in compression: if the report's verdict is nuanced ("competent hype, not a scam"), the post says that too. No rage-bait the report doesn't support.
- Never fabricate engagement bait ("everyone is talking about this").
- Each platform block must be paste-ready: correct length, line breaks, and links already positioned per PLATFORMS.md.
