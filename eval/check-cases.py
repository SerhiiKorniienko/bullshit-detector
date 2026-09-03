#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check every fixture case in eval/cases/ against the rules the corpus is built on.

The corpus is the ground truth the tool is measured against, so a case that quietly
breaks its own schema is worse than no case: the scorer reads it, produces a number,
and the number means nothing. Everything here is mechanical. Whether a label is
*right* is the owner's review, which this script cannot do and does not pretend to.

Usage:
    uv run eval/check-cases.py            # every case
    uv run eval/check-cases.py cases/<id> # one case

Exit 0 pass, 2 problems, 3 unreadable. Same convention as score.py and tally.py.
"""

import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

# One parse, one home: the case loader is score.py's, and the quote check is the gate's.
_s = importlib.util.spec_from_file_location("score", HERE / "score.py")
score = importlib.util.module_from_spec(_s)
_s.loader.exec_module(score)
tally = score.tally

TYPES = ("factual", "prediction", "opinion", "anecdote")
ROT = ("stable", "dated")
HEADER = ("schema", "id", "source_url", "source_title", "source_words", "fetched",
          "labeled", "labeled_by", "review_by", "prior_readings", "claims")


def check_case(case_dir: pathlib.Path) -> tuple[list, dict]:
    problems = []
    try:
        case = score.load_case(case_dir)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return [f"unreadable: {e}"], {}
    try:
        transcript = (case_dir / "transcript.md").read_text(encoding="utf-8")
    except OSError as e:
        return [f"no transcript: {e}"], {}
    nsrc = tally.quote_norm(transcript)

    for field in HEADER:
        if field not in case:
            problems.append(f"header: `{field}` is missing")
    if case.get("id") != case_dir.name:
        problems.append(f"header: id `{case.get('id')}` does not match directory `{case_dir.name}`")
    if not isinstance(case.get("prior_readings"), list):
        problems.append("header: `prior_readings` must be a list, empty when there are none")

    claims = case.get("claims") or []
    ids = {c["id"] for c in claims}
    stats = {"claims": len(claims), "labelled": 0, "null": 0, "load_bearing": 0,
             "pairs": 0, "dated": 0, "labels": {}}
    any_dated = False
    for c in claims:
        where = f"{c['id']}"
        quote = str(c.get("quote") or "")
        if len(quote.split()) < 3:
            problems.append(f"{where}: `quote` must be a verbatim span of at least three words; "
                            f"it is the claim's identifier across runs")
        elif not tally.span_in_source(quote, nsrc):
            problems.append(f'{where}: quote "{quote[:60]}" is not in transcript.md')
        if not str(c.get("claim") or "").strip():
            problems.append(f"{where}: `claim` is empty")
        if c.get("type") not in TYPES:
            problems.append(f"{where}: `type` must be one of {', '.join(TYPES)}")
        if not isinstance(c.get("load_bearing"), bool):
            problems.append(f"{where}: `load_bearing` must be true or false")
        if c.get("rot") not in ROT:
            problems.append(f"{where}: `rot` must be `stable` or `dated`")
        elif c["rot"] == "dated":
            any_dated = True
            stats["dated"] += 1

        label = c.get("label")
        if label is None:
            stats["null"] += 1
            if not str(c.get("basis") or "").strip():
                problems.append(f"{where}: a null label still needs a `basis` saying what was "
                                f"tried and why ground truth could not be established")
        else:
            stats["labelled"] += 1
            stats["labels"][label] = stats["labels"].get(label, 0) + 1
            if not str(c.get("basis") or "").strip():
                problems.append(f"{where}: labelled `{label}` with no `basis`")
            tol = c.get("tolerance")
            if not isinstance(tol, list) or not tol:
                problems.append(f"{where}: `tolerance` must be a non-empty list")
            else:
                bad = [t for t in tol if t not in score.VERDICT_NAMES]
                if bad:
                    problems.append(f"{where}: unknown verdicts in `tolerance`: {bad}")
                if label not in tol:
                    problems.append(f"{where}: `tolerance` must include the label itself")

        if c.get("load_bearing"):
            stats["load_bearing"] += 1
        other = c.get("pair")
        if other:
            partner = next((x for x in claims if x["id"] == other), None)
            if partner is None:
                problems.append(f"{where}: pair `{other}` does not exist")
            elif partner.get("pair") != c["id"]:
                problems.append(f"{where}: pair `{other}` does not point back")
            elif c["id"] < other:
                stats["pairs"] += 1

    if any_dated and not case.get("review_by"):
        problems.append("header: dated labels need a `review_by` date")
    return problems, stats


def main() -> int:
    targets = ([pathlib.Path(a) for a in sys.argv[1:]]
               or sorted(p for p in (HERE / "cases").iterdir() if p.is_dir()))
    failed = unreadable = 0
    for case_dir in targets:
        problems, stats = check_case(case_dir)
        if not stats:
            unreadable += 1
        elif problems:
            failed += 1
        mark = "✗" if problems else "✔"
        line = (f"{mark} {case_dir.name}: {stats['claims']} claims, {stats['labelled']} labelled, "
                f"{stats['null']} null, {stats['load_bearing']} load-bearing, {stats['pairs']} pairs, "
                f"{stats['dated']} dated; labels {stats['labels']}") if stats else f"{mark} {case_dir.name}"
        print(line)
        for p in problems:
            print(f"    {p}")
    if unreadable:
        return 3
    if failed:
        print(f"\n{failed} case(s) with problems", file=sys.stderr)
        return 2
    print(f"\n✔ {len(targets)} case(s) parse, every quote is in its transcript, "
          f"every labelled claim has a basis")
    return 0


if __name__ == "__main__":
    sys.exit(main())
