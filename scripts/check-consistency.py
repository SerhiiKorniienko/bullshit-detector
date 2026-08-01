#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Assert the verdict scale and score bands agree everywhere they are defined.

Usage:
    uv run scripts/check-consistency.py

Why this exists: the verdict scale is written down in five places and the score
bands in six, and on 2026-08-01 they disagreed. `render_carousel.py` was missing
`not checked`, so any carousel built from such a claim died with

    KeyError: 'not checked'

Nothing caught it because nothing compared the copies. The duplication itself is
deliberate — skills ship as independent directories and a cross-skill import
would break the moment someone installs one without the other — so the fix is not
a shared module, it is a test that the copies still match.

This reads the definitions rather than importing them: `render_carousel.py`
declares playwright as a dependency, so importing it would require a browser
stack to run a string comparison.

Exit codes: 0 everything agrees · 1 cannot read a definition · 2 they disagree.
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The canonical order and spelling. tally.py is the source of truth because it is
# the gate — if a renderer and the gate disagree, the gate is right by definition.
TALLY = ROOT / "skills/analysis/bullshit-detector/scripts/tally.py"
REPORT_CARD = ROOT / "skills/publishing/report-card/scripts/render_report.py"
CAROUSEL = ROOT / "skills/publishing/share/scripts/render_carousel.py"
RUBRIC = ROOT / "skills/analysis/bullshit-detector/RUBRIC.md"


def literal(path: Path, name: str):
    """Value of a module-level literal assignment, without importing the module."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        return None, f"cannot parse {path.relative_to(ROOT)}: {e}"
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets):
            try:
                return ast.literal_eval(node.value), None
            except ValueError as e:
                return None, f"{name} in {path.relative_to(ROOT)} is not a literal: {e}"
    return None, f"{name} not found in {path.relative_to(ROOT)}"


def verdict_sets():
    """(source label -> set of verdict names) for every file that defines them."""
    out, errors = {}, []

    v, err = literal(TALLY, "VERDICTS")          # [(glyph, name), ...]
    if err:
        errors.append(err)
    else:
        out["tally.py"] = {name for _, name in v}

    v, err = literal(REPORT_CARD, "VERDICTS")    # {name: (glyph, colour, label)}
    if err:
        errors.append(err)
    else:
        out["report-card"] = set(v)

    v, err = literal(CAROUSEL, "VERDICTS")       # {name: (colour, LABEL)}
    if err:
        errors.append(err)
    else:
        out["share carousel"] = set(v)

    return out, errors


def band_sets():
    """(source label -> tuple of band labels, in ascending score order)."""
    out, errors = {}, []

    v, err = literal(REPORT_CARD, "SCORE_BANDS")  # [(ceiling, label, bg, fg), ...]
    if err:
        errors.append(err)
    else:
        out["report-card"] = tuple(label for _, label, _, _ in v)

    # RUBRIC states them as prose: "- **0–2 Solid.**"
    try:
        rubric = RUBRIC.read_text(encoding="utf-8")
        found = re.findall(r"^-\s+\*\*\d+[–-]\d+\s+([A-Za-z][A-Za-z -]*?)\.\*\*", rubric, re.M)
        if found:
            out["RUBRIC.md"] = tuple(found)
        else:
            errors.append("no score bands found in RUBRIC.md")
    except OSError as e:
        errors.append(f"cannot read RUBRIC.md: {e}")

    return out, errors


def compare(what: str, groups: dict) -> list:
    """Report every source that differs from the gate/first source."""
    if len(groups) < 2:
        return []
    reference_name = next(iter(groups))
    reference = groups[reference_name]
    problems = []
    for name, value in groups.items():
        if value == reference:
            continue
        if isinstance(value, set):
            missing = sorted(reference - value)
            extra = sorted(value - reference)
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if extra:
                detail.append(f"unexpected {extra}")
            problems.append(f"{what}: {name} disagrees with {reference_name} — "
                            + ", ".join(detail))
        else:
            problems.append(f"{what}: {name} has {list(value)}, "
                            f"{reference_name} has {list(reference)}")
    return problems


def main() -> None:
    problems, errors = [], []

    verdicts, e = verdict_sets()
    errors += e
    problems += compare("verdict scale", verdicts)

    bands, e = band_sets()
    errors += e
    problems += compare("score bands", bands)

    for err in errors:
        print(f"  ! {err}", file=sys.stderr)
    if errors:
        sys.exit(1)

    for p in problems:
        print(f"  ✗ {p}")
    if problems:
        print(f"\n{len(problems)} inconsistenc{'y' if len(problems) == 1 else 'ies'}. "
              f"tally.py is the gate, so it is right by definition — fix the others.")
        sys.exit(2)

    print(f"✔ verdict scale agrees across {len(verdicts)} definitions "
          f"({', '.join(verdicts)})")
    print(f"✔ score bands agree across {len(bands)} definitions ({', '.join(bands)})")
    print("\nNote: korniienko.dev carries its own copies of the score bands "
          "(src/lib/score.ts, scripts/generate-og-images.js) and cannot be checked "
          "from this repo.")


if __name__ == "__main__":
    main()
