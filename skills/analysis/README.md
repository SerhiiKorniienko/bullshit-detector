# Analysis

Skills that reason about content. All are source-agnostic — they work on text regardless of where it came from, and use [fetch-content](../ingestion/fetch-content/SKILL.md) to get it.

## Model-invoked

Model- or user-reachable (rich trigger phrasing so the model reaches for them when you say "is this bullshit?" or "summarize this").

- **[bullshit-detector](./bullshit-detector/SKILL.md)** — Extract every claim, verify each against independent sources via web search, scan for hype signals, and produce a report card with per-claim verdicts (✅🟡🟠❌❓) and a 0–10 BS score.
- **[summarize](./summarize/SKILL.md)** — Structured TLDR with timestamped key points, notable quotes, and an honest "worth your time?" call.
- **[explain](./explain/SKILL.md)** — ELI5 → deep-dive explanation of the content or any concept in it, with a jargon glossary and the prerequisites the original assumes.
