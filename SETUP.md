# Setup guide

How to run these skills in different agents and apps. The skills are portable [Agent Skills](https://agentskills.io) — plain markdown + self-contained Python scripts — so the question is never "does my agent support this repo", it's "can my agent load a skills folder, run a shell script, and search the web".

**Requirements cheat-sheet:**

| Skill | Needs shell + [uv](https://docs.astral.sh/uv/) | Needs internet from scripts | Needs agent web search |
|---|---|---|---|
| `fetch-content` (YouTube/TikTok/articles/PDF) | ✅ | ✅ (yt-dlp reaches YouTube/TikTok) | — |
| `bullshit-detector` | — | — | ✅ (verdicts require sources) |
| `summarize`, `explain` | — | — | optional |
| `share` (carousel rendering) | ✅ | first run only (playwright chromium) | — |

---

## Claude Code CLI

Full support — this is the home turf. Two install paths (**pick one, not both**):

**skills.sh installer** (copies files, yours to hack on):

```bash
npx skills@latest add SerhiiKorniienko/bullshit-detector
```

**Claude Code plugin** (read-only bundle, auto-updates):

```
/plugin marketplace add SerhiiKorniienko/bullshit-detector
/plugin install bullshit-detector@serhii-korniienko
```

Then just ask: *"is this bullshit? \<url\>"*. Skills live in `~/.claude/skills/` (installer) or the plugin cache; Claude Code picks them up automatically.

Contributors: clone the repo and run `scripts/link-skills.sh` — it symlinks the promoted skills into `~/.claude/skills`, so repo edits are live instantly.

## Claude Desktop app: Code tab

The desktop app (macOS/Windows) has three tabs — **Chat**, **Cowork**, **Code**. The Code tab is full Claude Code and reads `~/.claude/skills/` exactly like the CLI ([docs](https://code.claude.com/docs/en/desktop)).

- Install once via either CLI path above — the Code tab sees the same skills, no extra steps.
- Plugins work too: **"+" next to the prompt → Plugins → Add plugin**, same marketplace config as the CLI.
- Everything works here: local shell, `uv`, yt-dlp, unrestricted network. This is the recommended way to use the full pipeline in a GUI.

Note: the **Cowork** tab is different — it sources skills from your claude.ai account ("Customize" in the sidebar), *not* from `~/.claude/skills`. Local skills don't carry over automatically.

## Claude Desktop and claude.ai: Chat

The Chat tab (and claude.ai on the web) supports custom skills on all plans, but they run in a code-execution sandbox with restricted networking — so only the **analysis** skills are practical here.

**Install:**

1. Enable code execution: **Settings → Capabilities → "Code execution and file creation"** ([docs](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)).
2. Zip a skill folder — the folder itself must be the ZIP root, with `SKILL.md` inside (e.g. zip the `bullshit-detector/` folder from `skills/analysis/`).
3. Upload: **Customize → Skills → "+" → Upload a skill** ([docs](https://support.claude.com/en/articles/12512180-use-skills-in-claude)).

**What works:** `bullshit-detector`, `summarize`, `explain` on text you paste or on articles Claude's built-in web search/fetch can reach. Chat has web search, so verification works.

**What doesn't:** `fetch-content` for YouTube/TikTok. The sandbox's network egress is limited to package registries by default on every plan (Team defaults to package managers only; Enterprise defaults to egress off), so yt-dlp can't reach video platforms ([docs](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)). Workaround: fetch the transcript on your machine (see [TikTok section in the README](./README.md#tiktok-videos)) and paste it into the chat.

## OpenAI Codex

The skills.sh installer supports multiple agents — run it and pick Codex when prompted:

```bash
npx skills@latest add SerhiiKorniienko/bullshit-detector
```

Notes:

- Skills are copied into the agent's skills directory. If your Codex version doesn't auto-discover skills, point to them from your `AGENTS.md` (e.g. "For fact-checking requests, follow the instructions in `<path>/bullshit-detector/SKILL.md`").
- `fetch-content` needs shell access and `uv` installed; approve network access for yt-dlp when Codex asks.
- The detector's verdicts require web search — enable Codex's web search, otherwise every claim comes back ❓ unverifiable (by design: the skill forbids confirming claims from model memory).

## ChatGPT

ChatGPT (web/desktop chat) has no Agent Skills support and no local shell, so the scripts can't run. Two workarounds:

- **Paste-driven:** open [`skills/analysis/bullshit-detector/SKILL.md`](./skills/analysis/bullshit-detector/SKILL.md), paste its contents as the first message, then paste the transcript/article text. Web search must be enabled for verification.
- **Custom GPT:** create a GPT with the SKILL.md contents (plus `RUBRIC.md`) as instructions. Same limitation: you supply the text, it does the judging.

For videos, fetch the transcript locally first (`uvx yt-dlp --write-auto-subs --skip-download <url>`) and paste it.

## Where the report ends up

Skill availability is only half the question. The other half is whether the artifact survives.

| Surface | Report lands in | Survives the session? |
|---|---|---|
| Claude Code CLI | `~/.bullshit-detector/reports/<YYYY>/` on your machine | ✅ yes |
| Desktop **Code** tab | same — it is the same filesystem | ✅ yes |
| Desktop / claude.ai **Chat** | the sandbox, which is per-conversation | ❌ no — download it |
| **Cowork** tab | sandbox, same caveat | ❌ no — download it |

**Local surfaces.** The report writes to `$BULLSHIT_DETECTOR_REPORTS` if you set it, otherwise
`~/.bullshit-detector/reports/<YYYY>/`. Deliberately **not** the temp directory: reports exist to be
re-read, diffed against a later run and compared across releases, and macOS runs a temp cleaner
nightly that quietly deletes exactly that evidence. Point the variable at a git repo if you want
them versioned:

```bash
export BULLSHIT_DETECTOR_REPORTS=~/reports   # in .zshrc / .bashrc
```

**Sandboxed surfaces.** The home directory may not be writable, in which case the skill falls back
to the temp directory and says so in its reply. The file dies with the conversation, so the thing
to take away is the **HTML** — `report-card` is stdlib-only and runs under plain `python3`, no `uv`
needed, and the page it produces is a single self-contained file with no external references. Save
it and it keeps working offline, forever.

Either way, **`tally.py` decides whether the report is sound** — exit 0 compliant, exit 2 not — and
`report-card` refuses to render a report that fails it. A good-looking page built from a report
that fails its own arithmetic is worse than no page.

## Other agents

**OpenCode, Cursor, Amp, Gemini CLI, …** — anything the skills.sh installer supports:

```bash
npx skills@latest add SerhiiKorniienko/bullshit-detector
```

The installer detects installed agents and copies the skills into each one's directory. For agents it doesn't know, the manual recipe is always the same:

1. Copy `skills/analysis/*`, `skills/ingestion/*`, `skills/publishing/*` into wherever your agent loads skills/instructions from (or reference the SKILL.md files from its context file — `AGENTS.md`, `GEMINI.md`, rules, etc.).
2. Make sure the agent can run shell commands and `uv` is installed (for `fetch-content` and `share`).
3. Make sure the agent has a web search tool (for `bullshit-detector`).

The SKILL.md bodies deliberately avoid agent-specific tool names ("use your web search tool", never a vendor tool name), so they read the same everywhere.
