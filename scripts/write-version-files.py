#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Write the manifest version into a VERSION file inside every promoted skill (#46).

The manifest lives three directories above the skill and does not travel with an
`npx skills add` install — only `skills/<bucket>/<skill>/` is copied — so every report
from that install path stamps `version unknown` and drops out of version-filed examples,
cross-release comparison, and the `*_SINCE` gate design. The fix is the banner rule:
a generated artifact, never hand-edited. The single source of truth stays
`.claude-plugin/plugin.json`; this script propagates it, and `tally.py --self-test`
fails loudly when a VERSION file drifts from the manifest, so a skipped regeneration
is caught at release time rather than shipped.

Usage:  uv run scripts/write-version-files.py        (run after every version bump)

Exit 0 on success, 1 when the manifest is unreadable.
"""

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / ".claude-plugin" / "plugin.json"


def main() -> int:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        version = manifest["version"]
        skills = manifest["skills"]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"ERROR: cannot read {MANIFEST}: {e}", file=sys.stderr)
        return 1

    for entry in skills:
        skill_dir = (REPO / entry).resolve()
        if not skill_dir.is_dir():
            print(f"ERROR: manifest lists {entry} but it is not a directory",
                  file=sys.stderr)
            return 1
        target = skill_dir / "VERSION"
        current = target.read_text(encoding="utf-8").strip() if target.exists() else None
        target.write_text(version + "\n", encoding="utf-8")
        state = "unchanged" if current == version else f"{current or 'absent'} → {version}"
        print(f"  {entry}/VERSION  {state}")
    print(f"✔ {len(skills)} skills carry {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
