Skills are organized into bucket folders under `skills/`:

- `analysis/` — skills that reason about content (source-agnostic, work on text)
- `ingestion/` — skills that turn sources into text (adapters live here)
- `publishing/` — skills that turn analysis results into shareable output (posts, carousels)
- `in-progress/` — drafts not yet ready to ship

Every skill in `analysis/`, `ingestion/`, or `publishing/` (the **promoted** buckets) must have a reference in the top-level `README.md` and an entry in `.claude-plugin/plugin.json`'s `skills` array — the Claude Code plugin ships exactly the promoted set. Skills in `in-progress/` must not appear in either. Each bucket folder has a `README.md` listing every skill in the bucket with a one-line description, skill name linked to its `SKILL.md`; the top-level `README.md` links every promoted skill the same way.

The repo is also its own single-plugin Claude Code marketplace: `.claude-plugin/marketplace.json` lists the one `bullshit-detector` plugin. When releasing, bump `.claude-plugin/plugin.json`'s `version` — Claude uses it to decide when installed users see an update. Run `claude plugin validate . --strict` after touching either manifest.

Architecture rule: analysis skills never fetch — they receive normalized text + metadata and reference the `fetch-content` skill for URLs. New sources are new adapters inside `skills/ingestion/fetch-content/scripts/fetch.py`; analysis skills must not change when a source is added. Keep skills portable: no agent-specific tool names in SKILL.md bodies ("use your web search tool", not "use WebSearch").

The detector's core integrity rule — verdicts require sources, never confirm/refute a claim from model memory — is load-bearing; don't weaken it when editing `skills/analysis/bullshit-detector/`.

Report bookkeeping is enforced, not instructed. `skills/analysis/bullshit-detector/scripts/tally.py` recounts a finished report's own claims table and exits 2 if the tally doesn't reconcile, the version stamp or source link is missing, a ❓ row doesn't say whether a search ran, a claim leans on "widely reported" with no `[N URLs → K origins]` marker, the count of claims dropped as ambiguous is absent, a claim kept under every reading isn't named, a row carries a searched verdict with nothing to click, or the one-line run footer is missing, misstates seconds-per-claim, or reports more searches than tool calls. Checks added after a release carry the version they start applying at (`AMBIG_SINCE`, `LINKED_EVIDENCE_SINCE`, `RUN_LINE_SINCE`, `AMBIG_READINGS_SINCE`, gated through `check_applies`) and are skipped for reports stamped older than that — judging an old report by new rules is the same error as re-scoring it with a new rubric. **A gated constant makes the next release number load-bearing:** gate a check at a version that never ships and it never fires, silently. This exists because three consecutive real runs got the tally wrong — off by 2, then by 8 — while the analysis in those same runs was sound: attention goes to the argument and the counting rots. **When a mechanical step keeps getting skipped, make the artifact invalid without it rather than adding another instruction.** Don't replace this with a workflow orchestrator — the steps that fail are scriptable, the steps that need sequencing are reasoning, and an orchestrator requiring subagents would break the portability rule above.

`fetch.py` is self-contained via PEP 723 inline dependencies and must stay runnable with plain `uv run` and with `python3` after a manual `pip install`. After changing it, smoke-test all adapters: a YouTube URL, a TikTok URL (`https://vt.tiktok.com/ZS4dhBje6` has eng-US captions), an article, a tweet (`https://x.com/naval/status/1002103360646823936` works), and a PDF.

The `agents/` directory ships with the Claude Code plugin (auto-discovered) and holds subagents that skills delegate to — e.g. `claim-extractor` pinned to a cheap model for parallel claim extraction on long transcripts. SKILL.md bodies must stay portable: reference such agents conditionally ("if your harness supports subagents…"), never as a hard requirement.

The README banner in `assets/` is generated, not hand-edited: `uv run scripts/render_banner.py`
writes `banner-light.png` and `banner-dark.png`, and the README picks between them with a
`<picture>` element. It carries **no version, score or claim count on purpose** — a number frozen
into an image is a number nobody remembers to update, and this repo cannot afford a stale figure on
its front page. Type is fitted to the box at render time rather than hardcoded, because a hardcoded
size clipped the title the first time the canvas width changed. Inter ships in `scripts/fonts/`
under the SIL OFL (`OFL.txt` travels with it).

To (re)link every promoted skill into the local harness skill directories (`~/.claude/skills`, `~/.agents/skills`), run `scripts/link-skills.sh`. Symlinks point into this repo, so `git pull` keeps them current; re-run after adding, removing, or renaming a skill.
