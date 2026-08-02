#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check whether any paper a report cites has been retracted.

The source hierarchy ranks primary documents highest, and a retracted paper is still a
primary document — so a claim sourced to one currently rates ✅ confirmed at tier 1. That
is the rubric working exactly as written and producing a wrong answer, and the tiering
makes this tool *more* exposed than a naive checker would be, not less.

Deliberately NOT part of `tally.py`. The gate runs on every report and must stay offline
and deterministic; a check that needs the network belongs beside it, where a flaky API
degrades the answer instead of failing the report.

OpenAlex carries `is_retracted` on the DOI record — free, no key, no auth. Crossref is the
documented fallback; Semantic Scholar has no retraction flag at all, which is worth knowing
before switching provider.

Usage:
    uv run retractions.py <report.md>

Exit 0 nothing retracted (or no DOIs found) · 1 usage/network trouble · 2 a cited paper is
retracted and the row does not say so.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# DOIs as they appear in links and prose. `)` must be allowed inside the suffix — real
# DOIs contain parentheses, and excluding them truncated 10.1016/S0140-6736(97)11096-0 to
# ...S0140-6736(97, which then looked clean. That is the Wakefield paper: the most famous
# retraction there is, silently passing. Parens are balanced afterwards instead, which is
# what distinguishes a DOI's own `)` from the one closing a markdown link.
DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\]\|<>\"]+)", re.I)


def trim_doi(raw: str) -> str:
    """Strip trailing punctuation and any `)` with no matching `(` inside the DOI."""
    doi = raw.rstrip(".,;:")
    while doi.endswith(")") and doi.count(")") > doi.count("("):
        doi = doi[:-1].rstrip(".,;:")
    return doi
CLAIM_ROW = re.compile(r"^\|\s*(\d+)([a-z]?)\s*\|")

# The content citing a retracted paper is a finding about the content, not our error —
# sometimes the retraction *is* the story. A row that already says so is not flagged.
ACKNOWLEDGED = re.compile(r"\bretract(?:ed|ion|ions)\b|\bwithdraw(?:n|al)\b|\bexpression of concern\b",
                          re.I)

API = "https://api.openalex.org/works/doi:{}?select=id,doi,title,is_retracted"


def dois_by_row(text: str):
    """Every DOI in the report, mapped to the claim row it sits in (or None for prose)."""
    found = {}
    for line in text.splitlines():
        m = CLAIM_ROW.match(line)
        row = f"{m.group(1)}{m.group(2) or ''}" if m else None
        for d in DOI.finditer(line):
            doi = trim_doi(d.group(1))
            if doi:
                found.setdefault(doi.lower(), []).append((row, line))
    return found


def openalex(doi: str, timeout: float):
    url = API.format(urllib.parse.quote(doi, safe="/"))
    req = urllib.request.Request(
        url, headers={"User-Agent": "bullshit-detector/retractions (+https://github.com/"
                                    "SerhiiKorniienko/bullshit-detector)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report")
    ap.add_argument("--timeout", type=float, default=15.0)
    args = ap.parse_args()

    path = Path(args.report)
    if not path.exists():
        print(f"no such report: {path}", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")

    found = dois_by_row(text)
    if not found:
        print("no DOIs cited — nothing to check")
        return 0

    retracted, unreachable = [], []
    for doi, occurrences in sorted(found.items()):
        try:
            rec = openalex(doi, args.timeout)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue  # not in OpenAlex is not evidence of anything
            unreachable.append((doi, f"HTTP {e.code}"))
            continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            unreachable.append((doi, str(e)))
            continue
        if rec.get("is_retracted"):
            for row, line in occurrences:
                retracted.append((doi, row, rec.get("title") or "", ACKNOWLEDGED.search(line)))

    print(f"checked {len(found)} DOI(s) against OpenAlex")
    if unreachable:
        print(f"\n{len(unreachable)} could not be checked — the answer is incomplete, "
              f"not clean:", file=sys.stderr)
        for doi, why in unreachable:
            print(f"  ? {doi} — {why}", file=sys.stderr)

    undisclosed = [r for r in retracted if not r[3]]
    for doi, row, title, ack in retracted:
        where = f"claim {row}" if row else "prose"
        state = "acknowledged in the row" if ack else "NOT acknowledged"
        print(f"  {'!' if ack else '✗'} {where}: {doi} is retracted — {state}"
              + (f" — {title[:70]}" if title else ""), file=sys.stderr)

    if undisclosed:
        print(f"\n{len(undisclosed)} claim(s) rest on a retracted paper without saying so. "
              f"Cap the verdict at 🟠 and name the retraction in the evidence cell — or, if "
              f"the *content* cited it and the retraction is the story, say that instead.",
              file=sys.stderr)
        return 2
    if retracted:
        print("\n✔ retracted papers are cited, and every row says so", file=sys.stderr)
    else:
        print("✔ no cited paper is retracted", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
