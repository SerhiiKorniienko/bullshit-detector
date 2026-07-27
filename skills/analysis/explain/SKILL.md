---
name: explain
description: Explain content or any concept inside it at the depth the user needs — ELI5, practitioner level, or expert deep-dive — with a jargon glossary and context the original assumes. Use when the user says "explain this", "what does X mean here", "break this down", "I don't understand this part", or shares content and asks how something in it works.
---

# explain

Make the content understandable without dumbing it down dishonestly.

## Workflow

1. **Get the text** (via `fetch-content` skill script if it's a URL, else web fetch or paste).
2. **Pick the depth** — from the user's request, or ask one short question if genuinely unclear:
   - **ELI5** — analogies, zero jargon, the core mechanism only
   - **Practitioner** — assumes general technical literacy, focuses on how it works and what to do with it
   - **Deep dive** — mechanisms, edge cases, history, competing views
3. **Explain**, structured as:
   - The one-sentence version first
   - The mechanism: how it actually works, step by step
   - **Glossary**: every jargon term the content uses without defining, one line each
   - **What the content assumes you know** — the missing prerequisites that made it confusing
   - Where the content's own explanation is wrong or oversimplified, if it is — flag it, don't repeat it

## Rules

- Explaining ≠ endorsing. If the content's claim is contested, present the explanation *and* note the contest ("the video asserts X; the standard view is Y").
- Analogies must survive scrutiny — say where the analogy breaks.
- If the user points at a specific segment ("the part at 12:30", "section 3"), explain that segment in the context of the whole, not in isolation.
- Don't pad: a concept that takes three sentences gets three sentences.
