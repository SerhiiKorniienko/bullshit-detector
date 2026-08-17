# Setup guide

Find your app below and follow its steps. For the at-a-glance "what works where" table, see the [README](./README.md#what-works-where) — this file is the walkthroughs.

(The skills are portable [Agent Skills](https://agentskills.io) — plain markdown + self-contained scripts — so the question is never "does my agent support this repo", it's "can it load a skills folder, run a script, and search the web". A per-skill requirements table for the technically curious sits [at the bottom](#under-the-hood-what-each-skill-needs).)

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

Cowork is the "do the work for me" side of Claude — the **Cowork** half of the Chat | Cowork toggle in the message box (a separate tab on older builds), on desktop and claude.ai. No terminal at any step: everything installs by pasting a link ([docs](https://claude.com/docs/cowork/guide/plugins)).

1. Open **Customize** in the sidebar → **Plugins**.
2. **Add marketplace** → paste `SerhiiKorniienko/bullshit-detector`.
3. Install **bullshit-detector** from the list that appears.

Then flip the toggle to **Cowork** and ask: *"is this bullshit? \<link\>"*.

What to expect:

- **Articles, tweets, PDFs, and pasted text** — work out of the box.
- **YouTube / TikTok videos** — turn on the **Claude in Chrome** connector first. Claude then opens the video in your own browser and reads the transcript straight off the page — in a real run it found the "Show transcript" button, clicked it, and read the panel by itself. No Chrome connector? Open the video, click **Show transcript** under the description, copy it, and paste it into the chat.
- **Download the report before closing the session.** Cowork works in a temporary cloud workspace that's discarded afterwards — ask for the HTML report card, download it, and it's yours forever.

*(Why videos need the extra step: that cloud workspace can't reach video sites on its own. The Chrome connector is Claude borrowing your browser, which can.)*

One boundary: plugins apply to Cowork and Code, not to the **Chat** side of the toggle — Chat has its own skill upload, next section.

## Claude Desktop and claude.ai: Chat

Chat can run the analysis skills — the detector, summarize, explain — on any text it can see. One-time setup:

1. Turn on **Settings → Capabilities → "Code execution and file creation"** ([docs](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)).
2. Get the skill onto your computer: on the [GitHub page](https://github.com/SerhiiKorniienko/bullshit-detector), green **Code** button → **Download ZIP**, unzip it, then zip just the `bullshit-detector` folder you'll find inside `skills/analysis/` (the folder itself, so `SKILL.md` sits one level down in the zip).
3. Upload it: **Customize → Skills → "+" → Upload a skill** ([docs](https://support.claude.com/en/articles/12512180-use-skills-in-claude)).

What to expect:

- **Pasted text and article links** — work. Chat has web search, so claims get verified against real sources.
- **YouTube / TikTok links — don't.** Chat can't reach video sites. Open the video, click **Show transcript** under the description, copy, paste it into the chat.
- Want summarize or explain here too? Repeat steps 2–3 with their folders — uploads are one skill per zip.

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

## Under the hood: what each skill needs

For contributors and the technically curious — nothing above requires this table.

| Skill | Needs shell + [uv](https://docs.astral.sh/uv/) | Needs internet from scripts | Needs agent web search |
|---|---|---|---|
| `fetch-content` (YouTube/TikTok/articles/PDF) | ✅ | ✅ (yt-dlp reaches YouTube/TikTok) | — |
| `bullshit-detector` | — | — | ✅ (verdicts require sources) |
| `summarize`, `explain` | — | — | optional |
| `share` (carousel rendering) | ✅ | first run only (playwright chromium) | — |
