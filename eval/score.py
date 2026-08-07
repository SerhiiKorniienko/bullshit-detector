#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Score a bullshit-detector run against a labelled fixture case (#3).

Offline and deterministic, same rule as tally.py: a gate that needs the network or a
model is a gate that gets skipped. Reads the curated labels from `cases/<id>/case.json`
and the run's claims from the report's `.claims.jsonl` sibling when one exists, else
from the markdown table using the same row shape the gate parses.

Usage:
    uv run eval/score.py cases/<id> report.md [report2.md ...]
    uv run eval/score.py cases/<id> --stability r1.md r2.md [...]
    options: --min-similarity 0.5  --threshold-true 0.95  --json

Exit 0 pass · 2 gate fail (known-true rate under threshold, or a laundered merge) ·
3 structural (unreadable case or report).
"""

import argparse
import importlib.util
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
CASE_SCHEMA = "bullshit-detector/eval-case@1"

# One parse, one home: the row regex and verdict-cell reader come from the gate itself,
# so a report the gate accepts is a report this scorer can read, always.
_spec = importlib.util.spec_from_file_location(
    "tally", REPO / "skills/analysis/bullshit-detector/scripts/tally.py")
tally = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tally)

VERDICT_NAMES = {name for _, name in tally.VERDICTS}
# The ordinal truth axis. ❓ and ⚪ are not on it — unverifiable is a statement about
# reachability, not truth — so kappa is computed over these four only.
SEVERITY = {"confirmed": 0, "plausible": 1, "misleading": 2, "false": 3}

STOP = {"the", "a", "an", "of", "to", "in", "and", "or", "is", "was", "are", "were",
        "that", "this", "it", "its", "for", "on", "at", "by", "with", "as", "be",
        "has", "have", "had", "not", "but", "they", "their", "you", "your"}


def tokens(s: str) -> frozenset:
    """Normalized content tokens. Digits always survive — numbers are what claims
    are made of here, and '500%' reduced to nothing would match everything."""
    words = re.sub(r"[^a-z0-9% ]+", " ", s.lower()).split()
    return frozenset(w for w in words
                     if (len(w) > 2 or any(c.isdigit() for c in w)) and w not in STOP)


def similarity(a: frozenset, b: frozenset) -> float:
    """Overlap coefficient: how much of the smaller span is inside the larger.

    The curated quote is a short span; the report's claim cell is that span plus
    decontextualisation. Jaccard punishes the length difference by design, which is
    exactly wrong here — containment is the relation being tested.
    """
    if not a or not b:
        return 0.0
    small, large = (a, b) if len(a) <= len(b) else (b, a)
    if len(small) < 3:      # two shared tokens is a coincidence, not a match
        return 0.0
    return len(small & large) / len(small)


# ---------------------------------------------------------------- loading

def load_case(case_dir: pathlib.Path) -> dict:
    case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    if case.get("schema") != CASE_SCHEMA:
        raise ValueError(f"case schema must be {CASE_SCHEMA}")
    seen = set()
    for c in case["claims"]:
        if c["id"] in seen:
            raise ValueError(f"duplicate claim id {c['id']}")
        seen.add(c["id"])
        label = c.get("label")
        if label is not None and label not in VERDICT_NAMES:
            raise ValueError(f"{c['id']}: unknown label {label}")
        if c.get("pair") and c["pair"] not in {x["id"] for x in case["claims"]}:
            raise ValueError(f"{c['id']}: pair points at unknown id {c['pair']}")
    return case


def load_rows(report: pathlib.Path) -> list:
    """The run's claims: [{n, text, verdict}]. Structured file first, prose second."""
    claims_path = report.with_name(
        (report.name[:-3] if report.name.endswith(".md") else report.name)
        + ".claims.jsonl")
    if claims_path.exists():
        claims, problems = tally.load_claims(claims_path)
        for p in problems:
            print(f"  ! {claims_path.name}: {p}", file=sys.stderr)
        return [{"n": str(c.get("n")),
                 "text": f"{c.get('claim', '')} {c.get('quote', '')}",
                 "verdict": c.get("verdict")} for c in claims]
    rows = []
    for line in report.read_text(encoding="utf-8").splitlines():
        m = tally.CLAIM_ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.split("|")]
        # | n | claim | type | verdict | evidence |  →  cells[1..5]
        rows.append({"n": m.group(1) + (m.group(2) or ""),
                     "text": cells[2] if len(cells) > 2 else "",
                     "verdict": tally.classify(line)})
    return rows


# ---------------------------------------------------------------- matching

def match(case: dict, rows: list, min_sim: float):
    """Greedy one-to-one on descending similarity, then a merge pass: an unmatched
    curated claim whose best row is already taken is recorded as merged into it."""
    row_toks = [tokens(r["text"]) for r in rows]
    scored = []
    for c in case["claims"]:
        ct = [tokens(c["quote"]), tokens(c["claim"])]
        for i, rt in enumerate(row_toks):
            s = max(similarity(t, rt) for t in ct)
            if s >= min_sim:
                scored.append((s, c["id"], i))
    scored.sort(key=lambda x: (-x[0], x[1], x[2]))

    matched, taken = {}, set()          # claim id → (row idx, sim)
    for s, cid, i in scored:
        if cid in matched or i in taken:
            continue
        matched[cid] = (i, s)
        taken.add(i)
    merged = {}                          # claim id → (row idx, sim), row already taken
    for s, cid, i in scored:
        if cid not in matched and cid not in merged and i in taken:
            merged[cid] = (i, s)
    return matched, merged


# ---------------------------------------------------------------- metrics

def qwk(pairs: list, k: int = 4):
    """Quadratic weighted kappa over ordinal categories 0..k-1."""
    n = len(pairs)
    if n < 2:
        return None
    observed = [[0] * k for _ in range(k)]
    for a, b in pairs:
        observed[a][b] += 1
    hist_a = [sum(row[j] for j in range(k)) for row in observed]
    hist_b = [sum(observed[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = (i - j) ** 2 / (k - 1) ** 2
            num += w * observed[i][j]
            den += w * hist_a[i] * hist_b[j] / n
    if den == 0:
        return None
    return 1.0 - num / den


def score_one(case: dict, report: pathlib.Path, args):
    try:
        rows = load_rows(report)
    except OSError as e:
        # The unattended-run failure path: claude -p exits 0 without writing the
        # report. A clean structural error, not a traceback — run-case.sh relies on it.
        print(f"ERROR: cannot read report {report}: {e}", file=sys.stderr)
        return None
    if not rows:
        print(f"ERROR: no claim rows found in {report}", file=sys.stderr)
        return None
    matched, merged = match(case, rows, args.min_similarity)
    reachable = {**matched, **merged}
    claims = {c["id"]: c for c in case["claims"]}

    # 1 — extraction recall, the settle-it-in-a-minute number
    total = len(claims)
    lb = [c for c in case["claims"] if c.get("load_bearing")]
    recall = len(reachable) / total if total else 0.0
    lb_recall = (sum(1 for c in lb if c["id"] in reachable) / len(lb)) if lb else None

    # 2 — the review queue: rows no curated claim reached
    used = {i for i, _ in matched.values()}
    queue = [r for i, r in enumerate(rows) if i not in used]

    # 3 — verdict agreement on every reachable labelled claim. Merged claims count:
    # the run chose to give one verdict to two assertions, so that verdict is graded
    # against both labels. Scoring only direct matches made a wrong verdict on a
    # merged claim invisible to every metric — found by adversarial review.
    exact = tolerated = 0
    confusion = {}
    kappa_pairs = []
    labelled = [cid for cid in reachable if claims[cid].get("label")]
    for cid in labelled:
        c = claims[cid]
        got = rows[reachable[cid][0]]["verdict"] or "not rated"
        want = c["label"]
        band = set(c.get("tolerance") or []) | {want}
        exact += got == want
        tolerated += got in band
        confusion[(want, got)] = confusion.get((want, got), 0) + 1
        if want in SEVERITY and got in SEVERITY:
            kappa_pairs.append((SEVERITY[want], SEVERITY[got]))
    kappa = qwk(kappa_pairs)

    # 4 — the gate number: known-true claims the run failed to confirm count against
    # it whether they were mis-graded or never extracted. A truth the run cannot find
    # is a truth the run cannot confirm.
    true_ids = [cid for cid, c in claims.items() if c.get("label") == "confirmed"]
    true_hits, true_missed_extraction = 0, 0
    for cid in true_ids:
        if cid in reachable:
            got = rows[reachable[cid][0]]["verdict"]
            band = set(claims[cid].get("tolerance") or []) | {"confirmed"}
            true_hits += got in band
        else:
            true_missed_extraction += 1
    true_rate = true_hits / len(true_ids) if true_ids else None

    # 5 — known-false catch rate: misleading-or-worse counts as caught
    false_ids = [cid for cid, c in claims.items() if c.get("label") == "false"]
    false_caught = sum(
        1 for cid in false_ids
        if cid in reachable
        and rows[reachable[cid][0]]["verdict"] in ("false", "misleading"))
    false_rate = false_caught / len(false_ids) if false_ids else None

    # 6 — merge behaviour: a merged verdict gentler than its harshest part is
    # laundering (#16), and it fails the gate.
    laundered, pair_warnings = [], []
    seen_pairs = set()
    for cid, c in claims.items():
        other = c.get("pair")
        if not other or (other, cid) in seen_pairs:
            continue
        seen_pairs.add((cid, other))
        a, b = reachable.get(cid), reachable.get(other)
        if not a or not b or a[0] != b[0]:
            continue                     # split or unextracted — recall covers it
        row_verdict = rows[a[0]]["verdict"]
        harshest = max((SEVERITY.get(claims[x].get("label"), -1) for x in (cid, other)))
        if harshest < 0:
            continue
        if row_verdict not in SEVERITY:
            pair_warnings.append(
                f"pair {cid}+{other} merged into row {rows[a[0]]['n']} rated "
                f"'{row_verdict or 'not rated'}' — dodges a known {harshest}-severity label")
        elif SEVERITY[row_verdict] < harshest:
            laundered.append(
                f"pair {cid}+{other} merged into row {rows[a[0]]['n']}: rated "
                f"{row_verdict}, harshest member label is severity {harshest}")

    return {
        "report": str(report),
        "rows": len(rows),
        "curated": total,
        "matched": len(matched),
        "merged": len(merged),
        "extraction_recall": round(recall, 3),
        "load_bearing_recall": round(lb_recall, 3) if lb_recall is not None else None,
        "review_queue": [{"n": r["n"], "text": r["text"][:120]} for r in queue],
        "verdicts_scored": len(labelled),
        "exact_agreement": round(exact / len(labelled), 3) if labelled else None,
        "tolerated_agreement": round(tolerated / len(labelled), 3) if labelled else None,
        "qwk": round(kappa, 3) if kappa is not None else None,
        "confusion": {f"{w}->{g}": n for (w, g), n in sorted(confusion.items())},
        "known_true": len(true_ids), "known_true_rate":
            round(true_rate, 3) if true_rate is not None else None,
        "known_true_missed_by_extraction": true_missed_extraction,
        "known_false": len(false_ids), "known_false_catch_rate":
            round(false_rate, 3) if false_rate is not None else None,
        "laundered_merges": laundered,
        "pair_warnings": pair_warnings,
        "matches": {cid: {"row": rows[i]["n"], "sim": round(s, 2)}
                    for cid, (i, s) in sorted(reachable.items())},
    }


def stability(case: dict, reports: list, args):
    """Same case, N runs: where do verdicts move? Includes 'unextracted' as a value —
    extraction instability is the measured 18–28-rows-from-one-video problem, not noise
    to hide."""
    per_run = []
    for r in reports:
        try:
            rows = load_rows(pathlib.Path(r))
        except OSError as e:
            print(f"ERROR: cannot read report {r}: {e}", file=sys.stderr)
            sys.exit(3)
        matched, merged = match(case, rows, args.min_similarity)
        reach = {**matched, **merged}
        per_run.append({cid: (rows[i]["verdict"] or "not rated")
                        for cid, (i, _) in reach.items()})
    table = {}
    for c in case["claims"]:
        table[c["id"]] = [run.get(c["id"], "unextracted") for run in per_run]
    flips = {cid: len(set(vs)) for cid, vs in table.items()}
    unanimous = sum(1 for n in flips.values() if n == 1)
    return {
        "runs": len(reports),
        "claims": len(table),
        "unanimous": unanimous,
        "unanimous_rate": round(unanimous / len(table), 3) if table else None,
        "mean_distinct_verdicts": round(sum(flips.values()) / len(flips), 2) if flips else None,
        "table": table,
    }


# ---------------------------------------------------------------- output

def show(result: dict, threshold: float):
    print(f"\n== {result['report']}")
    print(f"rows {result['rows']} · curated {result['curated']} · "
          f"matched {result['matched']} (+{result['merged']} merged)")
    print(f"extraction recall {result['extraction_recall']}"
          + (f" · load-bearing {result['load_bearing_recall']}"
             if result['load_bearing_recall'] is not None else ""))
    if result["verdicts_scored"]:
        print(f"verdicts: exact {result['exact_agreement']} · "
              f"tolerated {result['tolerated_agreement']} · "
              f"QWK {result['qwk'] if result['qwk'] is not None else 'n/a'} "
              f"(n={result['verdicts_scored']})")
        for k, v in result["confusion"].items():
            if k.split("->")[0] != k.split("->")[1]:
                print(f"    {k}: {v}")
    if result["known_true_rate"] is not None:
        flag = "PASS" if result["known_true_rate"] >= threshold else "FAIL"
        print(f"known-true confirm rate {result['known_true_rate']} "
              f"({result['known_true']} claims, "
              f"{result['known_true_missed_by_extraction']} lost to extraction) — {flag}")
    if result["known_false_catch_rate"] is not None:
        print(f"known-false catch rate {result['known_false_catch_rate']} "
              f"({result['known_false']} claims)")
    for w in result["pair_warnings"]:
        print(f"  warning: {w}")
    for l in result["laundered_merges"]:
        print(f"  LAUNDERED MERGE: {l}")
    weak = {cid: m for cid, m in result["matches"].items() if m["sim"] < 0.75}
    if weak:
        print(f"weak matches (sim < 0.75) — audit these pairings, --json for all:")
        for cid, m in sorted(weak.items()):
            print(f"    {cid} -> row {m['row']} (sim {m['sim']})")
    if result["review_queue"]:
        shown = result["review_queue"][:12]
        print(f"review queue — {len(result['review_queue'])} rows no curated claim "
              f"reached (padding, or curation gaps — a person decides; --json for all):")
        for r in shown:
            print(f"    row {r['n']}: {r['text']}")
        if len(result["review_queue"]) > len(shown):
            print(f"    … and {len(result['review_queue']) - len(shown)} more")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("case_dir")
    ap.add_argument("reports", nargs="+")
    ap.add_argument("--stability", action="store_true",
                    help="verdict flip table across runs instead of scoring")
    ap.add_argument("--min-similarity", type=float, default=0.5)
    ap.add_argument("--threshold-true", type=float, default=0.95,
                    help="gate: minimum known-true confirm rate")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        case = load_case(pathlib.Path(args.case_dir))
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    if args.stability:
        result = stability(case, args.reports, args)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"stability over {result['runs']} runs: "
                  f"{result['unanimous']}/{result['claims']} unanimous "
                  f"({result['unanimous_rate']}) · "
                  f"mean distinct verdicts {result['mean_distinct_verdicts']}")
            for cid, vs in result["table"].items():
                if len(set(vs)) > 1:
                    print(f"    {cid}: {' / '.join(vs)}")
        sys.exit(0)

    failed = False
    for r in args.reports:
        result = score_one(case, pathlib.Path(r), args)
        if result is None:
            sys.exit(3)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            show(result, args.threshold_true)
        if result["laundered_merges"]:
            failed = True
        if (result["known_true_rate"] is not None
                and result["known_true_rate"] < args.threshold_true):
            failed = True
    sys.exit(2 if failed else 0)


if __name__ == "__main__":
    main()
