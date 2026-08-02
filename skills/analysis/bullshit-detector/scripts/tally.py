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
import os
import sys
import unicodedata
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone, timedelta

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

# A claim number is an integer, optionally with a letter suffix: 6, 6a, 6b.
# Suffixes exist so that discovering mid-verification that one row holds a true
# and a false assertion can be fixed locally — split 6 into 6a/6b — instead of
# renumbering every row below it and rewriting every `rests on claim N`. A real
# run hit that and had to renumber fifteen rows. See #34, and #16 which asks for
# more splitting, not less.
CLAIM_ROW = re.compile(r"^\|\s*(\d+)([a-z]?)\s*\|", re.I)
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
UNREACHABLE_SINCE = (0, 12, 0)
DERIVED_M_SINCE = (0, 13, 0)
RUN_CLOCK_SINCE = (0, 13, 0)
UNREACHABLE_REASON_SINCE = (0, 13, 0)
QUOTE_INTEGRITY_SINCE = (0, 13, 0)

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
        numbers.append((int(m.group(1)), (m.group(2) or "").lower()))
        verdict = classify(line)
        if verdict:
            counts[verdict] += 1
            continue
        # Opinion / framework / prediction rows carry an explicit em-dash verdict.
        counts["not rateable"] += 1
        cells = [c.strip() for c in line.split("|")]
        if not any(c in {"—", "-", "–"} for c in cells):
            unmarked.append(m.group(1) + (m.group(2) or ""))
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


def numbering_problems(numbers: list) -> list:
    """Claim numbers must be gapless by ordinal, and unique once the suffix counts.

    `numbers` is [(ordinal, suffix)], so 6a/6b share ordinal 6. A split row is
    therefore legal and local; a bare 6 repeated is still a duplicate, and a
    missing ordinal is still a gap.
    """
    if not numbers:
        return []
    problems = []
    label = lambda n, sfx: f"{n}{sfx}"

    dupes = sorted({label(*k) for k, c in Counter(numbers).items() if c > 1})
    if dupes:
        problems.append(f"duplicate claim numbers: {dupes}")

    ordinals = {n for n, _ in numbers}
    gaps = sorted(set(range(1, max(ordinals) + 1)) - ordinals)
    if gaps:
        problems.append(f"missing claim numbers: {gaps}")

    # A suffix only means anything as part of a set. A lone 6a says a 6b was
    # meant to exist and reads as a numbering slip, not a deliberate split.
    by_ordinal = {}
    for n, sfx in numbers:
        by_ordinal.setdefault(n, []).append(sfx)
    for n, sfxs in sorted(by_ordinal.items()):
        marked = [x for x in sfxs if x]
        if not marked:
            continue
        if len(sfxs) == 1:
            problems.append(
                f"claim {n}{marked[0]} is the only row with that number — a suffix marks "
                f"a split, so it needs at least {n}a and {n}b, or drop the suffix")
        elif len(marked) != len(sfxs):
            problems.append(
                f"claim {n} mixes suffixed and bare rows — suffix all of them or none")
        else:
            want = [chr(ord('a') + i) for i in range(len(marked))]
            if sorted(marked) != want:
                problems.append(
                    f"claim {n} suffixes are {sorted(marked)}, expected {want} — "
                    f"split rows run a, b, c… with no gaps")
    return problems


def searched_count(text: str) -> int:
    """M — rows where a search actually ran.

    Every rated row except ⚪ not checked, minus ❓ rows declared `by construction`
    (nothing was searched because nothing could be). An undeclared ❓ row is counted
    the cautious way — it does *not* inflate M — and is reported separately by
    `undeclared_unverifiable`, so a missing declaration can never quietly raise the
    number the report is judged by.

    Since 0.13.0, **derived rows are out too**. `unlinked_evidence` already exempts a row
    that rests on another row from carrying a link of its own, on the grounds that its
    basis is a claim rather than a source — and a row exempted from needing its own
    evidence cannot also be counted as individually evidenced. Counting them inflated the
    one number RUBRIC tells a reader to judge the report by, and raised the bar on the
    `searches >= M` check, so the cheapest way to pass was to issue searches for rows the
    rules say cannot have one.

    The discriminator is the pair, not the phrase: a row is derived only when it rests on
    another claim *and* links nothing. A row that cites "claim 8" in passing while also
    sourcing its own figure did run a search, and still counts.
    """
    strict = check_applies(text, UNVERIFIABLE_TOKEN_SINCE)
    drop_derived = check_applies(text, DERIVED_M_SINCE)
    m = 0
    for line in text.splitlines():
        if not CLAIM_ROW.match(line):
            continue
        v = classify(line)
        if v is None or v == "not checked":
            continue
        if v == "unverifiable" and kind_of(line, strict) != "searched":
            continue
        if drop_derived and RESTS_ON_ROW.search(line) and not EVIDENCE_LINK.search(line):
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


# Substantive figures only: decimals, 4+ digit integers, percentages (symbol OR
# spelled out — the needle report writes "20 percent" in evidence against "20%" in
# the claim, and matching only the symbol made the strongest report in the corpus
# the one that cried wolf), and money. Not "3 weeks", not "two employees".
SUBSTANTIVE_NUMBER = re.compile(
    r"\d[\d,]*\.\d+\s*%?|\d[\d,]{3,}\s*%?|\d[\d,]*\s*(?:%|percent|per cent)"
    r"|[$£€]\s?\d|\d[\d,]*\s*(?:million|billion|trillion|bn|tn)", re.I)
UNREACHABLE_MENTION = re.compile(r"\*\*Unreachable:\s*(\d+)\s+sources?\*\*", re.I)

# Closed set, because the point of the field is counting causes across runs — six claims
# dead-ending at the same paywall is a finding, and free text cannot be aggregated.
# `empty` covers the case the original five missed: the fetch succeeded, the page returned
# 200, and there was no readable content behind it (a JS-only shell, a video page with no
# transcript, a PDF that extracted to nothing). That is not `blocked` — nothing refused
# us — and not `dead` — the URL resolves. Logging it as either loses the distinction that
# tells a later run whether a different fetcher would have helped.
UNREACHABLE_REASONS = {"paywall", "blocked", "dead", "timeout", "login", "empty"}


# Phrases that say the evidence went against the claim. Deliberately narrow: each one
# asserts a *finding*, not a hedge, so "unclear" and "not directly confirmed" are absent —
# those are what 🟡 is for.
CONTRADICTS = re.compile(
    r"\b(contradicted|contradicts|refuted|refutes|no record found|reverses the|"
    r"the opposite|is false|are false|does not hold|not supported by)\b", re.I)
# Anything gentler than ❌. The merge rule's floor is the harshest part, so a row with a
# contradicted half cannot settle at 🟠 either — 🟠 is exactly where claim 16 laundered it.
SOFT_VERDICTS = {"confirmed", "plausible", "misleading"}

# "so the claim isn't refuted" says the opposite of "refuted", and a warning that fires on
# it is the kind of noise that teaches people to ignore the channel. Checked against the
# text immediately before the marker; caught a real false positive in report-own-readme.
NEGATED = re.compile(
    r"\b(is|are|was|were|does|do|did|has|have|had|can|could|would)?n[’']?t\s+\w*\s*$"
    r"|\b(not|never|nothing|hardly|far from)\s+\w*\s*$", re.I)


def verdict_integrity_warnings(text: str) -> list:
    """Rows whose evidence leans harder than the verdict they carry. WARNING, never error.

    `examples/0.12.1/report-south-korea-ai-bubble.md` claim 16 merges two companies into
    one 🟠 row whose evidence says the second half is "contradicted" outright. Under the
    merge rule v0.12.1 itself shipped — a merged row is never gentler than its harshest
    part — that row is ❌. It passed every gate.

    Detecting a *merge* is not mechanically decidable, and a keyword list demanding one
    would be the magic-word failure of #33 over again. What is decidable is the mismatch:
    an evidence cell asserting the claim was contradicted, on a row rated ✅ or 🟡.

    This is a warning for the reason #28 puts numeric-consistency in the same tier — the
    exceptions are legitimate and reasonably common (an evidence cell may quote the
    content contradicting *itself*, or describe what a source refuted about a rival
    claim). Error severity may only test things that are binary. Nothing is rejected, `M`
    does not move, and the author resolves the row or splits it late into `16a`/`16b`.
    A warning also creates no incentive to game it: there is no gate to satisfy.
    """
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if not CLAIM_ROW.match(line):
            continue
        if classify(line) not in SOFT_VERDICTS:
            continue
        hit = next((h for h in CONTRADICTS.finditer(line)
                    if not NEGATED.search(line[max(0, h.start() - 40):h.start()])), None)
        if hit:
            num = CLAIM_ROW.match(line).group(1)
            out.append(
                f"claim {num} is rated {classify(line)} but its evidence says "
                f"\"{hit.group(0)}\" — if one part of the row is contradicted, the row "
                f"takes that verdict, or splits into {num}a/{num}b")
    return out


QUOTED_SPAN = re.compile(r'"([^"\n]{10,300})"')
ELLIPSIS = re.compile(r"\s*(?:\.\.\.|…)\s*")


def quote_norm(s: str) -> str:
    """Fold everything that varies between a transcript and a quotation of it.

    Smart quotes, dash flavours, casing, `[bracketed]` insertions the
    decontextualisation rule actively encourages, and punctuation the speaker never
    pronounced. What survives is the words.
    """
    s = unicodedata.normalize("NFKC", s)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        s = s.replace(a, b)
    s = re.sub(r"\[[^\]]*\]", " ", s)
    s = re.sub(r"[‐-―]", "-", s)
    s = re.sub(r"[^a-z0-9%$. ]", " ", s.lower())
    return " ".join(s.split())


def load_source(report_path: str, explicit: str | None):
    """The cached normalized text this report was written from, if it can be found.

    Explicit path wins, then $BULLSHIT_DETECTOR_SOURCE, then the convention in SKILL.md
    step 1 — `/tmp/bs-source-<slug>-<date>.md` beside a `bs-report-<slug>-<date>.md`.
    Returns None when nothing is found, and the caller skips rather than fails: the cache
    lives in a temp directory by design and a report checked a week later must not start
    failing because the machine swept it.
    """
    for cand in (explicit, os.environ.get("BULLSHIT_DETECTOR_SOURCE")):
        if cand and Path(cand).exists():
            return Path(cand).read_text(encoding="utf-8", errors="ignore")
    stem = Path(report_path).stem
    if stem.startswith("bs-report-"):
        guess = Path("/tmp") / f"bs-source-{stem[len('bs-report-'):]}.md"
        if guess.exists():
            return guess.read_text(encoding="utf-8", errors="ignore")
    return None


def quoted_spans(text: str):
    """Quotes that claim to be the content's own words: claim column + hype signals.

    Deliberately NOT the evidence column. Measuring the published 0.12.1 example found
    **0 of 13** evidence-cell quotes in the transcript — every one was a source headline
    or an outlet quoting a third party, which is what an evidence cell is *for*. The
    original design note had this backwards; checking evidence cells would fail every
    report while catching nothing.
    """
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if CLAIM_ROW.match(line):
            cells = line.split("|")
            if len(cells) > 2:
                for m in QUOTED_SPAN.finditer(cells[2]):
                    out.append((i, f"claim {CLAIM_ROW.match(line).group(1)}", m.group(1)))
    if "## Hype signals observed" in text:
        section = text.split("## Hype signals observed", 1)[1].split("\n## ", 1)[0]
        base = text[: text.index("## Hype signals observed")].count("\n") + 1
        for m in QUOTED_SPAN.finditer(section):
            out.append((base + section[: m.start()].count("\n"), "hype signals", m.group(1)))
    return out


def quote_integrity_problems(text: str, source: str) -> list:
    """A quoted span must be words the content actually contains.

    The failure a fact-checking tool cannot survive is a verdict rendered against words
    the speaker never said, and until the source cache landed there was nothing on disk
    to check against.

    An ellipsis marks elision, so `"A ... B"` is satisfied when A and B both appear, in
    order. Everything else must be present verbatim once normalized.
    """
    nsrc = quote_norm(source)
    problems = []
    for line_no, where, quote in quoted_spans(text):
        if len(quote.split()) < 5:
            continue
        parts = [p for p in ELLIPSIS.split(quote) if len(p.split()) >= 3]
        if not parts:
            continue
        pos, ok = 0, True
        for part in parts:
            np = quote_norm(part)
            if not np:
                continue
            found = nsrc.find(np, pos)
            if found < 0:
                ok = False
                break
            pos = found + len(np)
        if not ok:
            problems.append(
                f'{where} (line {line_no}) quotes "{quote[:70]}" — not in the source text. '
                f"Quote the content verbatim, mark elision with an ellipsis, and don't put "
                f"your own paraphrase in quotation marks")
    return problems


def numeric_consistency_warnings(text: str) -> list:
    """A row asserting a figure whose evidence engages no figure at all. WARNING.

    Severity is the whole design, per the rule this file already follows: quotes are
    binary and mechanically decidable, numbers are not. Legitimate derived arithmetic
    exists — this project's own rules *require* it — so erroring here would make the gate
    hostile to the sums it mandates. This flags candidates; it never blocks.
    """
    out = []
    for line in text.splitlines():
        if not CLAIM_ROW.match(line):
            continue
        v = classify(line)
        if v is None or v == "not checked":
            continue
        # A claim nobody outside the story could ever check has no figure to engage —
        # that is the finding, not a gap. Flagging it would fire hardest on exactly the
        # reports that handled unauditable numbers correctly.
        if v == "unverifiable" and kind_of(line, True) == "by construction":
            continue
        cells = line.split("|")
        if len(cells) < 6:
            continue
        claim, evidence = cells[2], cells[5]
        if not SUBSTANTIVE_NUMBER.search(claim):
            continue
        if SUBSTANTIVE_NUMBER.search(evidence) or RESTS_ON_ROW.search(evidence):
            continue
        out.append(
            f"claim {CLAIM_ROW.match(line).group(1)} asserts a figure but its evidence "
            f"cell contains no figure and names no row it rests on — the number was rated "
            f"without being engaged")
    return out


def _iso(value):
    """Parse an ISO-8601 stamp from a run record, tolerating a trailing Z."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def clock_problems(record: dict) -> list:
    """Anchor the reported duration to timestamps a reader can sanity-check.

    Everything else about the run line is checked for *internal* consistency: per-claim
    equals wall over M, searches never exceed tools, the line agrees with the record. A
    fabricated wall time satisfies all of it as long as the invented number is used
    consistently — which a real run did, drafting a plausible "27m40s" before it had
    finished and passing cleanly on the first try. Nothing tied the clock to anything
    outside the report.

    `wall_seconds` is fully derivable from `started` and `finished`, and auditing every
    record on disk found the constraint already holds everywhere but one shipped file
    (1080 recorded against a 1063-second span, undetected since 0.7.0). Exact, mechanical,
    no tolerance needed: a fabricated duration now requires inventing three fields in
    mutual agreement, and unlike a bare duration, timestamps are falsifiable against the
    report's own date.
    """
    started, finished = _iso(record.get("started")), _iso(record.get("finished"))
    recorded = record.get("wall_seconds")
    problems = []

    if started and finished:
        span = (finished - started).total_seconds()
        if span < 0:
            problems.append(
                f"run record `finished` precedes `started` by {abs(span):.0f}s")
        elif isinstance(recorded, (int, float)) and abs(span - recorded) > 1:
            problems.append(
                f"run record `wall_seconds` is {recorded:.0f} but `finished` − `started` "
                f"is {span:.0f} — the duration is derivable from the timestamps and must "
                f"match them, or the clock is anchored to nothing")
        if finished > datetime.now(timezone.utc) + timedelta(minutes=5):
            problems.append(
                f"run record `finished` ({record['finished']}) is in the future")
    elif recorded and not (started and finished):
        missing = [k for k in ("started", "finished") if not _iso(record.get(k))]
        problems.append(
            f"run record has `wall_seconds` but no parseable {' or '.join(missing)} — "
            f"a duration with no timestamps behind it cannot be checked against anything")
    return problems


def unreachable_problems(record: dict, text: str) -> list:
    """A run that logged blocked sources must say so in the report.

    RUBRIC already tells a row to say the evidence exists but couldn't be reached.
    That fires per row and then dies — nothing aggregates it, so a reader can't see
    that six claims dead-ended at the same paywalled outlet. Same shape as the
    run-line/run-record check: two places describing the same events must agree.
    """
    entries = record.get("unreachable")
    if not entries:
        return []
    if not isinstance(entries, list):
        return ["run record `unreachable` must be a list of {claim, url, reason}"]
    problems = []
    bad = [e for e in entries if not isinstance(e, dict) or not e.get("url")
           or not e.get("reason")]
    if bad:
        problems.append(
            f"{len(bad)} `unreachable` entr{'y' if len(bad) == 1 else 'ies'} missing url or "
            f"reason — each needs both, so a reader can tell a paywall from a dead link")
    if check_applies(text, UNREACHABLE_REASON_SINCE):
        unknown = sorted({e["reason"] for e in entries
                          if isinstance(e, dict) and e.get("reason")
                          and e["reason"] not in UNREACHABLE_REASONS})
        if unknown:
            problems.append(
                f"`unreachable` reason(s) {', '.join(unknown)} are not in the set "
                f"{', '.join(sorted(UNREACHABLE_REASONS))} — a free-text reason cannot be "
                f"counted across runs, which is the only thing this field is for")
    m = UNREACHABLE_MENTION.search(text)
    if not m:
        problems.append(
            f"run record lists {len(entries)} unreachable source(s), the report mentions none — "
            f"add `**Unreachable: N sources**` under the tally, or a reader cannot tell blocked "
            f"evidence from evidence that never existed")
    elif int(m.group(1)) != len(entries):
        problems.append(
            f"report says {m.group(1)} unreachable sources, the run record lists {len(entries)}")
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

    # Runs before the unreachable check — it is about the record's own contents and
    # must not be skipped just because the report has no run line.
    early = (unreachable_problems(record, text)
             if check_applies(text, UNREACHABLE_SINCE) else [])
    if check_applies(text, RUN_CLOCK_SINCE):
        early += clock_problems(record)

    line = RUN_LINE.search(text)
    if not line:
        return early
    problems, body = list(early), line.group(0)

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
    ap.add_argument("--source", help="cached normalized source text, for quote integrity")
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

    problems.extend(numbering_problems(numbers))
    if unmarked:
        problems.append(
            f"rows {unmarked} have no verdict at all — use a verdict glyph, or an "
            f'em-dash "—" for opinion/framework rows that are not rateable')
    undeclared = undeclared_unverifiable(text)
    if undeclared:
        problems.append(
            f"❓ rows {undeclared} don't declare their kind — "
            + (f"the verdict cell must read `❓ unverifiable (searched)` or "
               f"`❓ unverifiable (by construction)`, so M is recountable from the table and "
               f"can't be moved by wording in the evidence cell"
               if check_applies(text, UNVERIFIABLE_TOKEN_SINCE) else
               # An older report is judged by the rule it was written under, so it must
               # also be told about that rule. Quoting the current format at a 0.5.0
               # report describes a requirement that did not exist when it was written.
               f'each must say "searched; nothing found" or "unverifiable by '
               f'construction" so M is recountable'))

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

    source = load_source(args.report, args.source)
    if check_applies(text, QUOTE_INTEGRITY_SINCE):
        if source:
            problems.extend(quote_integrity_problems(text, source))
        else:
            print("note: source text not found — quote integrity not checked. Pass "
                  "--source or set $BULLSHIT_DETECTOR_SOURCE.", file=sys.stderr)

    warnings = verdict_integrity_warnings(text) + numeric_consistency_warnings(text)
    if warnings:
        print("\nWARNINGS (not blocking):", file=sys.stderr)
        for w in warnings:
            print(f"  ! {w}", file=sys.stderr)

    if problems:
        print("\nNON-COMPLIANT:", file=sys.stderr)
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        sys.exit(2)
    print("\n✔ tally reconciles and header checks pass", file=sys.stderr)


if __name__ == "__main__":
    main()
