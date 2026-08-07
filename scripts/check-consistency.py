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
SKILL = ROOT / "skills/analysis/bullshit-detector/SKILL.md"

# ---------------------------------------------------------------- one rule, one home
#
# #45's residue: 12 of 14 load-bearing rules were taught in both SKILL.md and RUBRIC.md
# in different words, and #35 proved that divergent re-teaching produces divergent runs
# that both pass the gate. The dedup happened; this stops it growing back.
#
# The metric the issue got stuck on — distinguishing *teaching* a rule from *pointing*
# at it — is resolved with a bright line that is mechanically decidable, per the repo's
# severity rule: a SPEC states a format with placeholders (`N claims extracted`, a
# definition table's header row); a concrete worked example (`35 claims extracted`) is
# a demonstration, not a second home, and pointers ("see RUBRIC.md") match nothing
# below. Each entry lists the spec's home and regexes that only the spec-form matches.
# The home must match EVERY pattern — a registry the home no longer matches is stale
# and fails loudly rather than silently checking nothing. The other file must match
# NONE.
#
# Matching runs on NORMALISED text — case-folded, all dash variants to '-', runs of
# spaces collapsed, line structure kept — so a mundane edit (an autocorrected en-dash,
# a doubled space, a case change) cannot smuggle a spec past the check. Adversarial
# review demonstrated exactly that evasion against the un-normalised first version.
# Honest limit, stated plainly: this catches a spec's *format* growing a second home.
# A rule re-taught in genuinely different words — new phrasing, no placeholder form —
# still evades any regex; that class is only caught by a person noticing, which is
# what #35 was. The check shrinks the surface, it does not close it.
ONE_HOME = [
    ("verdict scale definition table", SKILL, RUBRIC, [
        r"^\| ✅ confirmed \|",
        r"^\| ❓ unverifiable \*\(searched\)\* \|",
        r"^\| ❓ unverifiable \*\(by construction\)\* \|",
    ]),
    ("score bands", RUBRIC, SKILL, [
        r"^- \*\*0-2 solid\.\*\*",
        r"^- \*\*9-10 fabricated\.\*\*",
    ]),
    ("tally line format", RUBRIC, SKILL, [
        r"^>?\s*\*\*tally: n claims extracted, m individually source-checked",
    ]),
    ("ambiguous line format", RUBRIC, SKILL, [
        r"^>?\s*\*\*ambiguous: j claims dropped before verification; k checked under every reading",
    ]),
    ("source tier table", RUBRIC, SKILL, [
        r"^\| tier \| what it is \| examples \|",
    ]),
]


def normalise(text: str) -> str:
    """Case-fold, unify dashes, collapse horizontal whitespace. Lines survive, so ^
    anchors still mean 'start of line' after normalisation."""
    text = text.lower()
    text = re.sub(r"[–—−]", "-", text)
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines())


def one_home_problems() -> list:
    problems = []
    for rule, home, other, patterns in ONE_HOME:
        try:
            home_text = normalise(home.read_text(encoding="utf-8"))
            other_text = normalise(other.read_text(encoding="utf-8"))
        except OSError as e:
            problems.append(f"one-home: cannot read files for '{rule}': {e}")
            continue
        for p in patterns:
            if not re.search(p, home_text, re.M):
                problems.append(
                    f"one-home: '{rule}' registry is stale — {home.name} no longer "
                    f"matches {p!r}. Update the registry with the spec's new form; "
                    f"a pattern the home cannot match checks nothing.")
            if re.search(p, other_text, re.M):
                problems.append(
                    f"one-home: '{rule}' lives in {home.name}, but {other.name} "
                    f"also matches {p!r} — a second home. Replace it with a pointer.")
    return problems


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

    one_home = one_home_problems()
    problems += one_home

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
    print(f"✔ {len(ONE_HOME)} spec formats each live in exactly one of "
          f"SKILL.md / RUBRIC.md")
    print("\nNote: korniienko.dev carries its own copies of the score bands "
          "(src/lib/score.ts, scripts/generate-og-images.js) and cannot be checked "
          "from this repo.")


if __name__ == "__main__":
    main()
