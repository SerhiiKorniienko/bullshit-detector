#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Summarise what detector runs cost, from the run records they leave behind.

Usage:
    uv run scripts/runstats.py                    # every run record in /tmp
    uv run scripts/runstats.py /path/*.run.json   # specific ones
    uv run scripts/runstats.py --by-version       # group and average per release

This is a development tool. Nothing here appears in a report — a reader wants to know
whether the content is true, not how many searches it took to find out.

Why it exists: runs went from roughly 7 minutes to 12 across three releases and nobody
could say where the time went, so every proposed optimisation was a guess. The number
that matters is not wall time but seconds per checked claim — run 3 of one video took 9%
longer than run 2 while checking 53% more claims, which is the best run of the four by
cost and the worst by the clock.

Caveat that travels with every number here: the run records are written by the agent
about its own behaviour. Nothing recounts them. Treat them as indicative, and distrust
any single run — the same video checked four times produced 18/22/20/28 claims.
"""

import argparse
import glob
import json
import statistics
import sys
from pathlib import Path

DEFAULT_GLOB = "/tmp/bs-report-*.run.json"


def load(paths: list) -> list:
    runs = []
    for p in paths:
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"skipping {p}: {e}", file=sys.stderr)
            continue
        data["_path"] = p
        runs.append(data)
    return sorted(runs, key=lambda r: r.get("finished") or "")


def counts(run: dict) -> tuple:
    queries = run.get("queries") or []
    first = sum(1 for q in queries if q.get("pass") != "follow-up")
    return len(queries), first, len(queries) - first


def per_claim(run: dict):
    m = (run.get("claims") or {}).get("checked") or 0
    wall = run.get("wall_seconds") or 0
    return wall / m if m and wall else None


def fmt_wall(seconds) -> str:
    if not seconds:
        return "–"
    return f"{int(seconds) // 60}m{int(seconds) % 60:02d}s"


def row(run: dict) -> str:
    c = run.get("claims") or {}
    total, first, follow = counts(run)
    pc = per_claim(run)
    return (f"{(run.get('finished') or '?')[:10]:<11}"
            f"{run.get('version', '?'):<8}"
            f"{c.get('extracted', '–'):>4}"
            f"{c.get('checked', '–'):>4}"
            f"{c.get('dropped_ambiguous', '–'):>4}"
            f"{total:>7}"
            f"{f'{first}/{follow}':>8}"
            f"{run.get('coverage_checks', 0):>5}"
            f"{run.get('fetches', 0):>7}"
            f"{fmt_wall(run.get('wall_seconds')):>9}"
            f"{(f'{pc:.0f}s' if pc else '–'):>10}")


HEADER = (f"{'date':<11}{'version':<8}{'N':>4}{'M':>4}{'J':>4}"
          f"{'search':>7}{'1st/fu':>8}{'cov':>5}{'fetch':>7}{'wall':>9}{'per claim':>10}")


def inconsistencies(run: dict) -> list:
    """The run record is self-reported. Catch the parts that can disagree with themselves."""
    problems = []
    total, _, _ = counts(run)
    stated = run.get("searches")
    if stated is not None and stated != total:
        problems.append(f"says {stated} searches, lists {total} queries")
    c = run.get("claims") or {}
    if c.get("checked") and c.get("extracted") and c["checked"] > c["extracted"]:
        problems.append(f"checked {c['checked']} > extracted {c['extracted']}")
    if total and not run.get("wall_seconds"):
        problems.append("no wall time recorded")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("records", nargs="*", help=f"run records (default: {DEFAULT_GLOB})")
    ap.add_argument("--by-version", action="store_true",
                    help="average per release instead of listing every run")
    args = ap.parse_args()

    paths = args.records or sorted(glob.glob(DEFAULT_GLOB))
    if not paths:
        print(f"no run records found — looked for {DEFAULT_GLOB}", file=sys.stderr)
        sys.exit(1)
    runs = load(paths)
    if not runs:
        sys.exit(1)

    if args.by_version:
        print(f"{'version':<10}{'runs':>5}{'med N':>7}{'med M':>7}"
              f"{'med search':>12}{'med wall':>10}{'med/claim':>11}")
        by = {}
        for r in runs:
            by.setdefault(r.get("version", "?"), []).append(r)
        for version in sorted(by):
            group = by[version]
            pcs = [p for p in (per_claim(r) for r in group) if p]
            med = statistics.median
            print(f"{version:<10}{len(group):>5}"
                  f"{med([(r.get('claims') or {}).get('extracted', 0) for r in group]):>7.0f}"
                  f"{med([(r.get('claims') or {}).get('checked', 0) for r in group]):>7.0f}"
                  f"{med([counts(r)[0] for r in group]):>12.0f}"
                  f"{fmt_wall(med([r.get('wall_seconds') or 0 for r in group])):>10}"
                  f"{(f'{med(pcs):.0f}s' if pcs else '–'):>11}")
    else:
        print(HEADER)
        for r in runs:
            print(row(r))

    flagged = [(r, inconsistencies(r)) for r in runs]
    flagged = [(r, p) for r, p in flagged if p]
    if flagged:
        print("\nself-reported figures that disagree with themselves:", file=sys.stderr)
        for r, problems in flagged:
            print(f"  {Path(r['_path']).name}: {'; '.join(problems)}", file=sys.stderr)


if __name__ == "__main__":
    main()
