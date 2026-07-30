#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Count a BS report's own claims table and check the report's arithmetic.

Usage:
    uv run tally.py <report.md>          # print the correct tally + compliance check
    uv run tally.py <report.md> --fix    # rewrite the Tally line in place

Why this exists: across three real runs the tally was wrong every time — off by 2, then
by 8 — while the analysis itself was sound. Counting 47 table rows by eye is the kind of
work a model does badly and a script does perfectly. A fact-checking report whose own
arithmetic doesn't reconcile discredits every number above it, so this is not optional.

Exit codes: 0 all checks pass · 1 bad input · 2 report is non-compliant.
"""

import argparse
import re
import sys
from collections import Counter

VERDICTS = [
    ("✅", "confirmed"),
    ("🟡", "plausible"),
    ("🟠", "misleading"),
    ("❌", "false"),
    ("❓", "unverifiable"),
    ("⚪", "not checked"),
]
# Order the tally line reports them in.
RATED = ["confirmed", "plausible", "misleading", "false"]

CLAIM_ROW = re.compile(r"^\|\s*(\d+)\s*\|")
TALLY_LINE = re.compile(r"^>?\s*\*\*Tally:.*", re.M)
VERSION_STAMP = re.compile(r"bullshit-detector\s+v?(\d+)\.(\d+)\.(\d+)")
AMBIG_LINE = re.compile(r"\*\*Ambiguous:\s*(\d+)\s+claims?\s+dropped[^*]*\*\*\s*(.*)", re.I)
# Reports stamped by an older release were written under that release's rules. Checking
# them against rules added later is the same error as re-scoring an old report with a new
# rubric, so each check that postdates a release records the version it starts applying at.
AMBIG_SINCE = (0, 6, 0)


def classify(row: str):
    """Return the row's verdict, or None if it carries no verdict marker.

    Read the verdict *cell*, never the whole line. Evidence prose legitimately contains
    verdict glyphs — "Con 365 ✅; Labour won 202, not 203" sits in a 🟡 row — and matching
    anywhere in the line silently promotes those to confirmed. That bug inflated a real
    report's confirmed count by 2 before this was caught.
    """
    for cell in (c.strip() for c in row.split("|")):
        for glyph, name in VERDICTS:
            if cell.startswith(glyph):
                return name
    return None


def scan(text: str):
    counts = Counter()
    numbers, unmarked = [], []
    for line in text.splitlines():
        m = CLAIM_ROW.match(line)
        if not m:
            continue
        numbers.append(int(m.group(1)))
        verdict = classify(line)
        if verdict:
            counts[verdict] += 1
            continue
        # Opinion / framework / prediction rows carry an explicit em-dash verdict.
        counts["not rateable"] += 1
        cells = [c.strip() for c in line.split("|")]
        if not any(c in {"—", "-", "–"} for c in cells):
            unmarked.append(int(m.group(1)))
    return counts, numbers, unmarked


def searched_count(text: str) -> int:
    """M — rows where a search actually ran.

    Every rated row except ⚪ not checked, minus ❓ rows declared unverifiable by
    construction (nothing was searched because nothing could be).
    """
    m = 0
    for line in text.splitlines():
        if not CLAIM_ROW.match(line):
            continue
        v = classify(line)
        if v is None or v == "not checked":
            continue
        if v == "unverifiable" and re.search(r"by construction", line, re.I):
            continue
        m += 1
    return m


BREADTH = re.compile(
    r"widely reported|multiple outlets|many outlets|several outlets|reported by \w+ (?:and|,)"
    r"|dozens of|across \d+ outlets|everyone reported", re.I)
ORIGIN_MARK = re.compile(r"URLs?\s*→")


def breadth_without_origin(text: str) -> list:
    """Rows that lean on breadth of coverage but never counted the origins.

    "Widely reported" is the exact claim shape where eyeballing fails and a measured
    origin count changes the verdict — it is what coverage-check exists for. Flagging
    it here is deliberate: the cheapest way to satisfy the checker is to run the tool.
    """
    bad = []
    for line in text.splitlines():
        m = CLAIM_ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.split("|")]
        evidence = cells[-2] if len(cells) > 2 else ""
        if BREADTH.search(evidence) and not ORIGIN_MARK.search(evidence):
            bad.append(int(m.group(1)))
    return bad


def undeclared_unverifiable(text: str) -> list:
    """❓ rows that don't say whether a search actually ran.

    "Searched, found nothing" counts toward M; "unverifiable by construction" does not.
    The script will not guess from prose — the row has to declare it, which is exactly
    what RUBRIC.md asks for.
    """
    bad = []
    for line in text.splitlines():
        m = CLAIM_ROW.match(line)
        if m and classify(line) == "unverifiable" and not re.search(
                r"by construction|searched", line, re.I):
            bad.append(int(m.group(1)))
    return bad


def report_version(text: str):
    """The release the report says it was produced by, or None if unstamped.

    None means "current run against a manifest-less install" — new checks apply. An old
    version number means the report predates them and must not be judged by them.
    """
    m = VERSION_STAMP.search(text)
    return tuple(int(g) for g in m.groups()) if m else None


def ambiguous_line_problem(text: str):
    """The dropped-claims count next to the tally — required, and 0 is a real answer.

    Step 3 drops claims the content never disambiguates, so N is a filtered number. A
    filtered number that doesn't say it was filtered reads as a complete inventory, and
    the reader cannot tell "four checkable claims" from "four checkable claims and eleven
    that could mean anything". Counting what you threw away is exactly the bookkeeping
    that rots when it is merely instructed.
    """
    version = report_version(text)
    if version is not None and version < AMBIG_SINCE:
        return None
    m = AMBIG_LINE.search(text)
    if not m:
        return ("no ambiguous-claims line — state "
                "`**Ambiguous: J claims dropped before verification**` next to the Tally "
                "(J may be 0) so a filtered claim count can't read as a complete one")
    if int(m.group(1)) > 0 and not m.group(2).strip(" —–-\t"):
        return (f"{m.group(1)} claims dropped as ambiguous but the line doesn't say what "
                f"they were — a bare count can't be argued with")
    return None


def build_line(counts: Counter, total: int, m: int) -> str:
    rated = ", ".join(f"{counts[k]} {k}" for k in RATED if counts[k])
    tail = []
    if counts["unverifiable"]:
        tail.append(f"{counts['unverifiable']} unverifiable")
    if counts["not checked"]:
        tail.append(f"{counts['not checked']} not checked")
    if counts["not rateable"]:
        tail.append(f"{counts['not rateable']} not rateable")
    extra = f" {'; '.join(tail)}." if tail else ""
    return (f"**Tally: {total} claims extracted, {m} individually source-checked** — "
            f"{rated}.{extra}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Check a BS report's tally against its own table")
    ap.add_argument("report", help="path to the report markdown")
    ap.add_argument("--fix", action="store_true", help="rewrite the Tally line in place")
    args = ap.parse_args()

    try:
        text = open(args.report, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: cannot read {args.report}: {e}", file=sys.stderr)
        sys.exit(1)

    counts, numbers, unmarked = scan(text)
    total = len(numbers)
    if not total:
        print("ERROR: no claim rows found — expected a markdown table with numbered rows",
              file=sys.stderr)
        sys.exit(1)

    m = searched_count(text)
    correct = build_line(counts, total, m)

    problems = []

    dupes = [n for n, c in Counter(numbers).items() if c > 1]
    if dupes:
        problems.append(f"duplicate claim numbers: {sorted(dupes)}")
    gaps = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
    if gaps:
        problems.append(f"missing claim numbers: {gaps}")
    if unmarked:
        problems.append(
            f"rows {unmarked} have no verdict at all — use a verdict glyph, or an "
            f'em-dash "—" for opinion/framework rows that are not rateable')
    undeclared = undeclared_unverifiable(text)
    if undeclared:
        problems.append(
            f"❓ rows {undeclared} don't say whether a search ran — each must state "
            f'"searched; nothing found" or "unverifiable by construction" so M is recountable')

    if not VERSION_STAMP.search(text):
        problems.append("no version stamp — header must carry `bullshit-detector <version>`")
    ambiguous = ambiguous_line_problem(text)
    if ambiguous:
        problems.append(ambiguous)
    if not re.search(r"\*\*Source:\*\*.*\]\(https?://", text):
        problems.append("no linked source URL in the header")
    breadth = breadth_without_origin(text)
    if breadth:
        problems.append(
            f"rows {breadth} rest on breadth of coverage with no origin count — run "
            f"coverage-check on them, or collapse the sources by hand and record "
            f"`[N URLs → K origins]`")

    existing = TALLY_LINE.search(text)
    if not existing:
        problems.append("no Tally line found")
    elif existing.group(0).strip().lstrip(">").strip().rstrip(".") != correct.strip().rstrip("."):
        problems.append("Tally line disagrees with the table")

    print(f"claim rows: {total}   searched (M): {m}")
    for _, name in VERDICTS:
        if counts[name]:
            print(f"  {name:14} {counts[name]}")
    if counts["not rateable"]:
        print(f"  {'not rateable':14} {counts['not rateable']}")
    print()
    print(correct)

    if args.fix and existing:
        prefix = "> " if existing.group(0).lstrip().startswith(">") else ""
        open(args.report, "w", encoding="utf-8").write(
            text[:existing.start()] + prefix + correct + text[existing.end():])
        print("\n✔ Tally line rewritten", file=sys.stderr)
        problems = [p for p in problems if not p.startswith("Tally line")]

    if problems:
        print("\nNON-COMPLIANT:", file=sys.stderr)
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        sys.exit(2)
    print("\n✔ tally reconciles and header checks pass", file=sys.stderr)


if __name__ == "__main__":
    main()
