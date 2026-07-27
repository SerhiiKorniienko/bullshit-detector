---
name: summarize
description: Produce a structured summary of a video, article, tweet thread, or PDF — TLDR, key points with timestamps/locations, notable quotes, and who should read/watch it. Use when the user asks to summarize a link or file, wants a TLDR, or asks "what does this video/article say" / "is this worth watching".
---

# summarize

Give someone the content without the runtime.

## Workflow

1. **Get the text.** If the input is a URL and the `fetch-content` skill is installed, use its script; otherwise use your web fetch tool or ask for a paste. Keep the metadata.
2. **Read fully**, then write:

```markdown
# <title>
**<author> · <platform> · <date> · <duration/length> · <views if notable>**

**TLDR:** one paragraph, ≤3 sentences — the actual thesis, not the topic.

## Key points
Bulleted. Each point = one idea, with [timestamp] or [p.N] so the
reader can jump to it. Preserve the content's own structure (if it
promises "14 ways", list all 14 — compressed, not truncated).

## Notable quotes
1–3 verbatim quotes that carry the content's voice, with locations.

## Worth your time?
One honest sentence per audience: who gains from the full version,
who is fine with this summary.
```

## Rules

- Summarize what the content says, not what you think of it (that's the `bullshit-detector` skill — mention it if the content smells hyped, don't perform its job here).
- Numbers, names, and claims must come from the content verbatim — no rounding, no "improving".
- If the content is listicle-shaped, the summary must contain the complete list. Never "...and 9 more ways".
- Scale length to source: a tweet gets 3 lines, a 3-hour podcast gets a full page.
