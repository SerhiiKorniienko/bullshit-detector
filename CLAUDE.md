Skills are organized into bucket folders under `skills/`:

- `analysis/` — skills that reason about content (source-agnostic, work on text)
- `ingestion/` — skills that turn sources into text (adapters live here)
- `publishing/` — skills that turn analysis results into shareable output (posts, carousels)
- `in-progress/` — drafts not yet ready to ship

Every skill in `analysis/`, `ingestion/`, or `publishing/` (the **promoted** buckets) must have a reference in the top-level `README.md` and an entry in `.claude-plugin/plugin.json`'s `skills` array — the Claude Code plugin ships exactly the promoted set. Skills in `in-progress/` must not appear in either. Each bucket folder has a `README.md` listing every skill in the bucket with a one-line description, skill name linked to its `SKILL.md`; the top-level `README.md` links every promoted skill the same way.

The repo is also its own single-plugin Claude Code marketplace: `.claude-plugin/marketplace.json` lists the one `bullshit-detector` plugin. When releasing, bump `.claude-plugin/plugin.json`'s `version` — Claude uses it to decide when installed users see an update. Run `claude plugin validate . --strict` after touching either manifest.

Architecture rule: analysis skills never fetch — they receive normalized text + metadata and reference the `fetch-content` skill for URLs. New sources are new adapters inside `skills/ingestion/fetch-content/scripts/fetch.py`; analysis skills must not change when a source is added. Keep skills portable: no agent-specific tool names in SKILL.md bodies ("use your web search tool", not "use WebSearch").

The detector's core integrity rule — verdicts require sources, never confirm/refute a claim from model memory — is load-bearing; don't weaken it when editing `skills/analysis/bullshit-detector/`.

`fetch.py` is self-contained via PEP 723 inline dependencies and must stay runnable with plain `uv run` and with `python3` after a manual `pip install`. After changing it, smoke-test all adapters: a YouTube URL, an article, a tweet (`https://x.com/naval/status/1002103360646823936` works), and a PDF.

To (re)link every promoted skill into the local harness skill directories (`~/.claude/skills`, `~/.agents/skills`), run `scripts/link-skills.sh`. Symlinks point into this repo, so `git pull` keeps them current; re-run after adding, removing, or renaming a skill.
