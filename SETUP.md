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

The desktop app (macOS/Windows) has two surfaces: **Home** — where the message box carries a **Chat | Cowork** toggle — and **Code**. (Older builds show Chat, Cowork, Code as three separate tabs.) The Code tab is full Claude Code and reads `~/.claude/skills/` exactly like the CLI ([docs](https://code.claude.com/docs/en/desktop)).

- Install once via either CLI path above — the Code tab sees the same skills, no extra steps.
- Plugins work too: **"+" next to the prompt → Plugins → Add plugin**, same marketplace config as the CLI.
- Everything works here: local shell, `uv`, yt-dlp, unrestricted network. This is the recommended way to use the full pipeline in a GUI.

Note: the **Cowork** tab is different — local skills don't carry over automatically. It has its own no-terminal install path, next section.

## Claude Cowork (no terminal)

Cowork — the non-developer surface in the desktop app and on claude.ai — installs the whole bundle as a plugin from a GitHub URL ([docs](https://claude.com/docs/cowork/guide/plugins)). On current desktop builds it's the **Cowork half of the Chat | Cowork toggle** in the message box on Home, not a separate tab. No terminal at any step:

1. Open **Customize** in the sidebar → **Plugins**.
2. **Add marketplace** → enter `SerhiiKorniienko/bullshit-detector` (the `owner/repo` shorthand works, so does the full GitHub URL).
3. Install **bullshit-detector** from the marketplace that appears, then open the plugin to see its skills.

Caveats that matter here:

- **Video fetching depends on the Chrome connector.** Cowork sessions default to an isolated cloud sandbox whose network egress is limited to package registries, and YouTube blocks datacenter IPs on top of that — so `fetch-content` itself can't pull YouTube/TikTok transcripts from inside Cowork. With **Claude in Chrome** connected, Cowork routes around this on its own: observed in a real run, it opens the video in your browser, clicks YouTube's "Show transcript" button, and reads the panel — your session, your IP, so nothing blocks it. Slower than the script (a couple dozen browser actions), but the full video pipeline works. Without the Chrome connector: articles, tweets, PDFs, and pasted text work; for a video, fetch the transcript on your machine ([README → TikTok section](./README.md#tiktok-videos)) and paste it.
- **Plugins don't reach the Chat tab.** Anthropic's docs are explicit: plugins are available in Cowork and Code, "they aren't used in Chat". For Chat, upload skill zips instead (next section).
- The report lands in the sandbox, which dies with the conversation — download the HTML before you close it (see [Where the report ends up](#where-the-report-ends-up)).

## Claude Desktop and claude.ai: Chat

The Chat tab (and claude.ai on the web) supports custom skills on all plans, but they run in a code-execution sandbox with restricted networking — so only the **analysis** skills are practical here.

**Install:**

1. Enable code execution: **Settings → Capabilities → "Code execution and file creation"** ([docs](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)).
2. Zip a skill folder — the folder itself must be the ZIP root, with `SKILL.md` inside (e.g. zip the `bullshit-detector/` folder from `skills/analysis/`).
3. Upload: **Customize → Skills → "+" → Upload a skill** ([docs](https://support.claude.com/en/articles/12512180-use-skills-in-claude)).

**What works:** `bullshit-detector`, `summarize`, `explain` on text you paste or on articles Claude's built-in web search/fetch can reach. Chat has web search, so verification works.

**What doesn't:** `fetch-content` for YouTube/TikTok. The sandbox's network egress is limited to package registries by default on every plan (Team defaults to package managers only; Enterprise defaults to egress off), so yt-dlp can't reach video platforms ([docs](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)). Workaround: fetch the transcript on your machine (see [TikTok section in the README](./README.md#tiktok-videos)) and paste it into the chat.

## OpenAI Codex

Codex reads Agent Skills natively — repo-level `.agents/skills/` and user-level `~/.agents/skills/`, built on the same [agentskills.io](https://agentskills.io) standard ([OpenAI's skills doc](https://learn.chatgpt.com/docs/build-skills)). The skills.sh installer puts them in the right place — run it and pick Codex when prompted:

```bash
npx skills@latest add SerhiiKorniienko/bullshit-detector
```

Notes:

- `fetch-content` needs shell access and `uv` installed; approve network access for yt-dlp when Codex asks.
- The detector's verdicts require web search — enable Codex's web search, otherwise every claim comes back ❓ unverifiable (by design: the skill forbids confirming claims from model memory).
- Per OpenAI's doc, standalone skills also load in the **ChatGPT desktop app** and the Codex IDE extension — same folders, no extra install.

## ChatGPT

The **desktop app** loads standalone Agent Skills from the same directories Codex uses (see above), so the skills.sh install covers it. On **chatgpt.com without the desktop app** there's no skills folder and no local shell, so the scripts can't run — two workarounds:

- **Paste-driven:** open [`skills/analysis/bullshit-detector/SKILL.md`](./skills/analysis/bullshit-detector/SKILL.md), paste its contents as the first message, then paste the transcript/article text. Web search must be enabled for verification.
- **Custom GPT:** create a GPT with the SKILL.md contents (plus `RUBRIC.md`) as instructions. Same limitation: you supply the text, it does the judging.

For videos, fetch the transcript locally first (`uvx yt-dlp --write-auto-subs --skip-download <url>`) and paste it.

## GitHub Copilot CLI

Copilot reads SKILL.md skills natively — project-level `.github/skills/`, `.claude/skills/`, `.agents/skills/`; personal `~/.copilot/skills/`, `~/.agents/skills/` ([docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)). The skills.sh installer covers it, and if you've already installed for another agent, the `~/.agents/skills/` copy is picked up as-is.

- `fetch-content` needs shell + `uv`; approve the commands when Copilot asks.
- Verdicts need a web search tool. If your Copilot surface doesn't have one, every claim comes back ❓ unverifiable — that's the skill refusing to judge from memory, not a bug.

## Cursor

Native skills since Cursor 2.4 — project `.cursor/skills/` or `.agents/skills/`, user `~/.cursor/skills/` or `~/.agents/skills/` ([docs](https://cursor.com/docs/context/skills)). Two installs:

- skills.sh installer (pick Cursor when prompted), or
- in-app: **Customize → Rules → Remote Rule (GitHub)** → paste the repo URL.

Cursor's agent has web search, so verification works out of the box.

## Gemini CLI

Native skills — user `~/.gemini/skills/` or `~/.agents/skills/`, workspace `.gemini/skills/` or `.agents/skills/` ([docs](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md)). The skills.sh installer covers it; Gemini also ships its own installer —

```bash
gemini skills install https://github.com/SerhiiKorniienko/bullshit-detector
```

— then `/skills list` in a session to confirm. If your version doesn't find the nested skill folders, fall back to the skills.sh installer. Web search (Google Search grounding) is built in, which is exactly what the detector needs.

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

**OpenCode, Zed, Amp, Goose, Cline, Factory Droid, …** — anything the skills.sh installer supports (75 agents at last count):

```bash
npx skills@latest add SerhiiKorniienko/bullshit-detector
```

The installer detects installed agents and copies the skills into each one's directory. Most of these also read `~/.agents/skills/` directly — the convergence directory of the [Agent Skills standard](https://agentskills.io) — so one install tends to cover several agents. For agents the installer doesn't know, the manual recipe is always the same:

1. Copy `skills/analysis/*`, `skills/ingestion/*`, `skills/publishing/*` into wherever your agent loads skills/instructions from (or reference the SKILL.md files from its context file — `AGENTS.md`, `GEMINI.md`, rules, etc.).
2. Make sure the agent can run shell commands and `uv` is installed (for `fetch-content` and `share`).
3. Make sure the agent has a web search tool (for `bullshit-detector`).

The SKILL.md bodies deliberately avoid agent-specific tool names ("use your web search tool", never a vendor tool name), so they read the same everywhere.
