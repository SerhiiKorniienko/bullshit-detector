#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Symlink every shipped skill into the local skill directories of each agent harness.

Dev-only, for maintainers:
  - ~/.claude/skills  — Claude Code
  - ~/.agents/skills  — Codex and other Agent Skills-compatible harnesses
Each entry is a symlink into this repo, so `git pull` keeps installed skills up to
date. Re-run after adding, removing, or renaming a skill. End users install via
skills.sh or the Claude Code plugin instead.

This was a shell script until 0.14.3, and the Anthropic plugin directory held every
scanned version for a reviewer on it (UNREAD_ASSET_REFERENCED, "could reach" a bundled
image). The two shell scripts it did not flag share its shebang and its repo-root
lookup; the only thing this one did that they did not was create symlinks and delete
directories at paths computed at run time. Same behaviour, now in Python like every
other maintainer script.

Usage:  uv run scripts/link-skills.py

Exit 0 on success, 1 when a destination is itself a symlink into this repo.
"""

import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP = {"in-progress", "deprecated"}


def shipped_skills() -> list[Path]:
    """Every directory under skills/ holding a SKILL.md, drafts and retired skills excluded."""
    found = []
    for root, dirs, files in os.walk(REPO / "skills"):
        dirs[:] = sorted(d for d in dirs if d not in SKIP)
        if "SKILL.md" in files:
            found.append(Path(root))
    return found


def main() -> int:
    skills = shipped_skills()
    for dest in (Path.home() / ".claude" / "skills", Path.home() / ".agents" / "skills"):
        # A destination that is itself a link into the repo would make every entry
        # below a link inside the repo pointing at the repo.
        if dest.is_symlink():
            resolved = dest.resolve()
            if resolved == REPO or REPO in resolved.parents:
                print(f"error: {dest} is a symlink into this repo ({resolved}).", file=sys.stderr)
                print(f'Remove it (rm "{dest}") and re-run.', file=sys.stderr)
                return 1

        dest.mkdir(parents=True, exist_ok=True)

        for src in skills:
            target = dest / src.name
            # A real copy (an earlier installer run) is replaced; a link is re-pointed.
            if target.exists() and not target.is_symlink():
                shutil.rmtree(target) if target.is_dir() else target.unlink()
            if target.is_symlink():
                target.unlink()
            target.symlink_to(src)
            print(f"linked {src.name} -> {src} ({dest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
