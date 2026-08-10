#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Assert every published example report still passes its own gate.

Usage:
    uv run scripts/check-examples.py

The examples are the tool's evidence: they are what a reader clicks before
deciding whether any of this is serious. A rule change that makes an old report
fail `tally.py` should surface here rather than in a reader's hands.

Reports written before the version stamp existed are skipped. `check_applies`
gates a check on the version in the header, so a report with no stamp cannot be
judged by the rules it was written under, and judging it by the current ones is
the same error as re-scoring it with a new rubric. Every skip is printed —
a file dropped in silence reads exactly like a file that passed.

Whether a report is stamped is decided with tally.py's own regexes rather than a
second copy of them. Two checks reading the same text for different purposes
must share one parse, or satisfying one silently changes the other. tally.py
declares no dependencies, so importing it costs nothing.

Exit codes: 0 all stamped examples pass · 1 nothing to check · 2 one failed.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TALLY = ROOT / "skills/analysis/bullshit-detector/scripts/tally.py"


def load_tally():
    spec = importlib.util.spec_from_file_location("tally", TALLY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    tally = load_tally()
    reports = sorted(ROOT.glob("examples/*/report-*.md"))
    if not reports:
        print("no example reports found", file=sys.stderr)
        return 1

    failed, checked, skipped = [], 0, 0
    for path in reports:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if not (tally.VERSION_STAMP.search(text) or tally.VERSION_UNKNOWN.search(text)):
            print(f"skipped {rel} (no version stamp, predates the gate)")
            skipped += 1
            continue
        # The subprocess exit code is tally.py's published contract; calling into
        # its internals would test a different thing than the gate a report faces.
        run = subprocess.run(
            [sys.executable, str(TALLY), str(path)],
            capture_output=True,
            text=True,
        )
        checked += 1
        if run.returncode == 0:
            print(f"ok      {rel}")
        else:
            print(f"FAILED  {rel}")
            print(run.stdout or run.stderr)
            failed.append(rel)

    print(f"\n{checked} checked, {skipped} skipped, {len(failed)} failed")
    if failed:
        print("✗ a published example no longer passes its own gate: "
              + ", ".join(str(f) for f in failed), file=sys.stderr)
        return 2
    print("✔ every stamped example still passes its own gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
