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
import json
import re
import sys
from pathlib import Path
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
AMBIG_LINE = re.compile(
    r"\*\*Ambiguous:\s*(\d+)\s+claims?\s+dropped"               # J — could not be pinned down
    r"(?:[^*]*?;\s*(\d+)\s+checked under every reading)?"       # K — kept, invariant verdict
    r"[^*]*\*\*\s*(.*)", re.I)
# Reports stamped by an older release were written under that release's rules. Checking
# them against rules added later is the same error as re-scoring an old report with a new
# rubric, so each check that postdates a release records the version it starts applying at.
# ⚠️ These must move with the release they ship in — a check gated at a version that never
# ships never fires, and the failure is silent.
AMBIG_SINCE = (0, 6, 0)
LINKED_EVIDENCE_SINCE = (0, 6, 1)
RUN_LINE_SINCE = (0, 7, 0)
AMBIG_READINGS_SINCE = (0, 8, 0)
SPONSORED_SINCE = (0, 9, 0)
UNVERIFIABLE_TOKEN_SINCE = (0, 11, 0)

RUN_LINE = re.compile(r"\*run:[^*]*\*", re.I)
RUN_WALL = re.compile(r"(?:(\d+)h)?(\d+)m(\d+)s")
RUN_FIELD = {name: re.compile(rf"{name}\s+(\d+)", re.I)
             for name in ("searches", "tools", "coverage")}
RUN_PER_CLAIM = re.compile(r"per claim\s+(\d+)s", re.I)
# A run record logs one entry per lookup; only the search ones count as searches.
FETCH_ENTRY = re.compile(r"^\s*(?:fetch\b|https?://)", re.I)
SEARCH_QUERIES = lambda entries: sum(
    1 for e in entries if not FETCH_ENTRY.match(str(e.get("q", ""))))

EVIDENCE_LINK = re.compile(r"\]\(https?://")
RESTS_ON_ROW = re.compile(r"\b(?:see |per |from )?claims?\s*#?\s*\d+", re.I)

# Advertorial published under a reputable masthead. The tier belongs to the
# advertiser, not the publisher (RUBRIC, "Tier the document, not the domain"),
# and the signal is right there in the URL — so a row citing one without saying
# so is mechanically detectable. Restricting search to reputable domains raises
# the share of these rather than lowering it: five of twenty top results in
# experiments/2026-07-30-search-api-access.md.
SPONSORED_URL = re.compile(
    r"https?://(?:"
    # host starts with a sponsored subdomain: sponsored.bloomberg.com
    r"(?:sponsored|partners|paidpost|advertorial)\.[^\s)]*"
    # or a sponsored path segment anywhere: ft.com/partnercontent/...
    r"|[^\s)]*?/(?:sponsored|partner-?content|brandfeatures|brand-?features"
    r"|branded|paid-?post|media-campaign|advertorial|promoted)(?:[/?#][^\s)]*|\b)"
    r")", re.I)
# Wording that shows the row already knows what it is citing.
SPONSORED_DECLARED = re.compile(
    r"tier\s*4|sponsor|advertorial|branded|partner content|paid[- ]for"
    r"|paid post|advertisement|promoted|in partnership with|presented by", re.I)


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


UNVERIFIABLE_KIND = re.compile(r"\(\s*(searched|by construction)\s*\)", re.I)


def unverifiable_kind(line: str):
    """Which kind of ❓ this row declares: 'searched', 'by construction', or None.

    One parse, used by BOTH the M count and the declaration check. They used to be
    two regexes over the same text pulling opposite ways: the declaration check
    rejected a ❓ row unless the word "searched" or "by construction" appeared
    anywhere in it, and the M count then keyed on those same words. So a validator
    that demanded a word got the word — and the word silently decided M, which is
    the number RUBRIC tells readers to judge the report by. A real 0.10.0 run hit
    exactly that and reported having to "insert the exact keywords".

    Since 0.11.0 the declaration lives in the *verdict cell* as a parenthetical, so
    it cannot be satisfied by evidence prose that happens to mention searching.
    Older reports fall back to the prose scan they were written under.
    """
    for cell in (c.strip() for c in line.split("|")):
        if cell.startswith("❓"):
            m = UNVERIFIABLE_KIND.search(cell)
            return m.group(1).lower() if m else None
    return None


def unverifiable_kind_legacy(line: str):
    """Pre-0.11.0 behaviour: grep the whole row."""
    if re.search(r"by construction", line, re.I):
        return "by construction"
    if re.search(r"searched", line, re.I):
        return "searched"
    return None


def kind_of(line: str, strict: bool):
    return unverifiable_kind(line) if strict else unverifiable_kind_legacy(line)


def searched_count(text: str) -> int:
    """M — rows where a search actually ran.

    Every rated row except ⚪ not checked, minus ❓ rows declared `by construction`
    (nothing was searched because nothing could be). An undeclared ❓ row is counted
    the cautious way — it does *not* inflate M — and is reported separately by
    `undeclared_unverifiable`, so a missing declaration can never quietly raise the
    number the report is judged by.
    """
    strict = check_applies(text, UNVERIFIABLE_TOKEN_SINCE)
    m = 0
    for line in text.splitlines():
        if not CLAIM_ROW.match(line):
            continue
        v = classify(line)
        if v is None or v == "not checked":
            continue
        if v == "unverifiable" and kind_of(line, strict) != "searched":
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
    """❓ rows that don't say which kind they are.

    Shares `kind_of` with `searched_count` on purpose — one parse decides both, so
    the two can no longer disagree about the same row. See `unverifiable_kind`.
    """
    strict = check_applies(text, UNVERIFIABLE_TOKEN_SINCE)
    bad = []
    for line in text.splitlines():
        m = CLAIM_ROW.match(line)
        if m and classify(line) == "unverifiable" and kind_of(line, strict) is None:
            bad.append(int(m.group(1)))
    return bad


SOURCE_LINE = re.compile(r"^\*\*Source:\*\*.*", re.M)
LINKED_URL = re.compile(r"\]\(https?://")
NO_PERMALINK = re.compile(
    r"no (?:stable |public |web |permanent |direct )?(?:permalink|url|link)", re.I)


def source_link_problem(text: str):
    """The header must let a reader reach the thing being judged — or say why they can't.

    Requiring a link outright made an entire legitimate class of report permanently
    non-compliant: pasted text, local files, deleted posts, and the draft-checking
    workflow, none of which have a permalink. RUBRIC.md already tells those reports to
    say so rather than link something approximate, so the validator has to accept that
    answer instead of demanding a URL that would be a fabrication.
    """
    line = SOURCE_LINE.search(text)
    if not line:
        return "no `**Source:**` line in the header"
    if LINKED_URL.search(line.group(0)) or NO_PERMALINK.search(line.group(0)):
        return None
    return ("header has no source link and doesn't say why — link the content, or state "
            "`no permalink` with the reason (a paste, a local file, a deleted post)")


def report_version(text: str):
    """The release the report says it was produced by, or None if unstamped.

    None means "current run against a manifest-less install" — new checks apply. An old
    version number means the report predates them and must not be judged by them.
    """
    m = VERSION_STAMP.search(text)
    return tuple(int(g) for g in m.groups()) if m else None


def gate_constants_shippable(manifest: Path) -> list:
    """Every `*_SINCE` must be <= the version in the manifest.

    A check gated at a version that never ships never fires, and does so silently —
    the report passes, the rule looks enforced, and nothing says otherwise. That
    failure is called out in CLAUDE.md; this is the check that makes it loud. It runs
    on `--self-test` rather than on every report, because it is a fact about the repo
    rather than about the report being validated.
    """
    try:
        current = tuple(int(p) for p in
                        json.loads(manifest.read_text())["version"].split("."))
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as e:
        return [f"could not read the manifest version from {manifest}: {e}"]
    bad = []
    for name, value in sorted(globals().items()):
        if not name.endswith("_SINCE") or not isinstance(value, tuple):
            continue
        if value > current:
            bad.append(
                f"{name} = {'.'.join(map(str, value))} is ahead of the manifest "
                f"({'.'.join(map(str, current))}) — this check can never fire. Bump the "
                f"manifest before shipping, or lower the constant.")
    return bad


def check_applies(text: str, since: tuple) -> bool:
    """Whether a check added in release `since` should judge this report."""
    version = report_version(text)
    return version is None or version >= since


def unlinked_evidence(text: str) -> list:
    """Rows carrying a searched verdict whose evidence links nothing.

    Every v0.6.0 report checked came back 100% unlinked — the reports named their
    sources ("reported by Bloomberg, CNBC, TechCrunch") and linked none of them, so a
    reader had to redo the search to check any claim. The documented marker format was
    `[4 URLs → 1 origin]`, which is not a link in markdown, and the tool did what the
    docs showed.

    Skips the rows where nothing was searched, and rows that say they rest on another
    claim — a derived figure's evidence legitimately lives in the row it derives from.
    """
    bad = []
    for line in text.splitlines():
        m = CLAIM_ROW.match(line)
        if not m:
            continue
        verdict = classify(line)
        if verdict is None or verdict == "not checked":
            continue
        if verdict == "unverifiable" and re.search(r"by construction", line, re.I):
            continue
        if EVIDENCE_LINK.search(line) or RESTS_ON_ROW.search(line):
            continue
        bad.append(int(m.group(1)))
    return bad


def undeclared_sponsored(text: str) -> list:
    """Rows citing advertorial without saying that is what it is.

    Tiering by domain reads `ft.com/partnercontent/comarch/...` as tier 2 when it is
    the advertiser talking about itself under a masthead it paid for. That is the
    existing "a source about itself is tier 4" rule one level down, and unlike most of
    this file's subject matter it is decidable from the URL alone — so it is checked
    rather than instructed.

    Only the *undeclared* case fails. Citing sponsored content is legitimate, and
    sometimes the advertorial is the story; a row that names it has done the work.
    """
    bad = []
    for line in text.splitlines():
        m = CLAIM_ROW.match(line)
        if not m:
            continue
        hit = SPONSORED_URL.search(line)
        if not hit:
            continue
        # Look for the declaration in the PROSE, not the whole row: every URL this
        # fires on contains "sponsored" or "partner content" by construction, so
        # searching the raw line lets the link declare itself and the check passes
        # on exactly the rows it exists to catch.
        prose = re.sub(r"https?://[^\s)]*", " ", line)
        if not SPONSORED_DECLARED.search(prose):
            bad.append((int(m.group(1)), hit.group(0)[:70]))
    return bad


def run_line_problems(text: str, m: int) -> list:
    """The one-line cost footer, and the two things about it that can be checked.

    Nothing here proves the run issued the searches it claims — a finished report cannot
    carry that proof. But two of the figures are derivable from the others, so a report
    that misstates them says so out loud:

    - `per claim` must be the wall time over M. Stated fresh, it would drift from the
      tally the way every hand-maintained number in this project eventually has.
    - `searches` cannot exceed `tools`, because issuing a search *is* a tool call. A real
      report claimed 31 claims individually source-checked against 15 tool calls, which
      is not possible, and nothing in the artifact made that visible. Now it does.
    """
    if not check_applies(text, RUN_LINE_SINCE):
        return []
    line = RUN_LINE.search(text)
    if not line:
        return ["no run line — end the report with "
                "`*run: 16m55s, searches 24, tools 30, coverage 1, per claim 44s*`"]
    body, problems = line.group(0), []
    values = {}
    for name, pattern in RUN_FIELD.items():
        found = pattern.search(body)
        if not found:
            problems.append(f"run line has no `{name}` count")
        else:
            values[name] = int(found.group(1))

    if {"searches", "tools"} <= values.keys() and values["searches"] > values["tools"]:
        problems.append(
            f"run line: {values['searches']} searches from {values['tools']} tool calls — "
            f"a search is a tool call, so this reports more work than was done")

    if "searches" in values and m and values["searches"] < m:
        problems.append(
            f"run line: {m} claims individually source-checked from {values['searches']} "
            f"searches — every claim carrying a verdict needs its own search, so this "
            f"reports more verification than was performed")

    wall, per = RUN_WALL.search(body), RUN_PER_CLAIM.search(body)
    if not wall:
        problems.append("run line has no wall time")
    elif per and m:
        seconds = int(wall.group(1) or 0) * 3600 + int(wall.group(2)) * 60 + int(wall.group(3))
        expected = round(seconds / m)
        if abs(expected - int(per.group(1))) > 1:
            problems.append(
                f"run line: {seconds}s over {m} checked claims is {expected}s per claim, "
                f"not {per.group(1)}s")
    return problems


def run_record_problems(report_path: str, text: str, m: int) -> list:
    """Cross-check the report's footer against the run record beside it.

    Both are written by the same run about the same events, and until this existed
    nothing compared them: tally.py read only the report, runstats.py read only the
    record. A real run reported 21 searches in its footer and logged 29 in its record,
    and both artifacts passed every check they had.

    Two numbers for one quantity, reconciled nowhere, is the failure this project exists
    to catch in other people's work.
    """
    record_path = Path(report_path).with_suffix(".run.json")
    if not record_path.exists():
        return []
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"run record beside the report is unreadable: {e}"]

    line = RUN_LINE.search(text)
    if not line:
        return []
    problems, body = [], line.group(0)

    queries = record.get("queries") or []
    searches = SEARCH_QUERIES(queries)
    stated = RUN_FIELD["searches"].search(body)
    if stated and searches and int(stated.group(1)) != searches:
        problems.append(
            f"run line says {stated.group(1)} searches, the run record lists {searches} — "
            f"one number, counted twice, disagreeing")

    wall = RUN_WALL.search(body)
    recorded = record.get("wall_seconds")
    if wall and recorded:
        seconds = int(wall.group(1) or 0) * 3600 + int(wall.group(2)) * 60 + int(wall.group(3))
        if abs(seconds - recorded) > max(60, 0.2 * recorded):
            problems.append(
                f"run line says {seconds}s, the run record says {recorded}s")

    claims = record.get("claims") or {}
    if claims.get("checked") not in (None, m):
        problems.append(
            f"run record says {claims['checked']} claims checked, the table says {m}")
    return problems


def ambiguous_line_problem(text: str):
    """The dropped-claims count next to the tally — required, and 0 is a real answer.

    Step 3 drops claims the content never disambiguates, so N is a filtered number. A
    filtered number that doesn't say it was filtered reads as a complete inventory, and
    the reader cannot tell "four checkable claims" from "four checkable claims and eleven
    that could mean anything". Counting what you threw away is exactly the bookkeeping
    that rots when it is merely instructed.

    Since 0.8.0 the line carries a second number: claims that had more than one reading,
    were checked under all of them, and reached the same verdict either way. Those are
    kept as table rows, so `J` alone could not describe them and reports were writing
    "0 dropped" next to prose admitting two claims were ambiguous — true, and unreadable.
    """
    if not check_applies(text, AMBIG_SINCE):
        return None
    m = AMBIG_LINE.search(text)
    if not m:
        return ("no ambiguous-claims line — state "
                "`**Ambiguous: J claims dropped before verification**` next to the Tally "
                "(J may be 0) so a filtered claim count can't read as a complete one")
    prose = m.group(3).strip(" —–-\t")
    if int(m.group(1)) > 0 and not prose:
        return (f"{m.group(1)} claims dropped as ambiguous but the line doesn't say what "
                f"they were — a bare count can't be argued with")
    if check_applies(text, AMBIG_READINGS_SINCE):
        kept = int(m.group(2)) if m.group(2) else 0
        # Only the mechanical half is enforced: say *which rows* you kept. Whether the
        # readings themselves are adequately described is a judgement, and a regex that
        # pretended to check it would pass on the word "reading" and fail on "base pay
        # vs total comp" — rejecting the better line of the two.
        if kept > 0 and not RESTS_ON_ROW.search(prose):
            return (f"{kept} claims kept under every reading but the line doesn't say which "
                    f"claims — name the rows, and the readings each one carried")
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
    ap.add_argument("report", nargs="?", help="path to the report markdown")
    ap.add_argument("--fix", action="store_true", help="rewrite the Tally line in place")
    ap.add_argument("--self-test", action="store_true",
                    help="check this script's own version gates against the manifest")
    args = ap.parse_args()

    if args.self_test:
        manifest = Path(__file__).resolve().parents[4] / ".claude-plugin" / "plugin.json"
        problems = gate_constants_shippable(manifest)
        for p in problems:
            print(f"  \u2717 {p}")
        print("\u2714 every version gate can fire" if not problems
              else f"{len(problems)} unshippable gate constant(s)")
        sys.exit(2 if problems else 0)

    if not args.report:
        ap.error("a report path is required (or use --self-test)")

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
            f"❓ rows {undeclared} don't declare their kind — the verdict cell must read "
            f"`❓ unverifiable (searched)` or `❓ unverifiable (by construction)`, so M is "
            f"recountable from the table and can't be moved by wording in the evidence cell")

    if not VERSION_STAMP.search(text):
        problems.append("no version stamp — header must carry `bullshit-detector <version>`")
    ambiguous = ambiguous_line_problem(text)
    if ambiguous:
        problems.append(ambiguous)
    problems.extend(run_line_problems(text, m))
    problems.extend(run_record_problems(args.report, text, m))
    if check_applies(text, LINKED_EVIDENCE_SINCE):
        unlinked = unlinked_evidence(text)
        if unlinked:
            problems.append(
                f"rows {unlinked} carry a searched verdict with nothing to click — link "
                f"the origin marker, or the source itself, so a reader can check the call "
                f"without redoing the search")
    if check_applies(text, SPONSORED_SINCE):
        for row, url in undeclared_sponsored(text):
            problems.append(
                f"row {row} cites sponsored content without naming it: {url} — "
                f"advertorial carries the advertiser's tier, not the publisher's, so "
                f"say `[tier 4: <publisher> partner content]` and cap the verdict at 🟡")
    source_problem = source_link_problem(text)
    if source_problem:
        problems.append(source_problem)
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
