#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Assert no worked example in the skill instructions is quoted from content we measure on.

A rule taught with an example lifted from a real transcript cannot be measured on that
transcript: the run reads the answer before it reads the content. `SKILL.md` taught the
invented-term rule with "algorithm authority", a phrase spoken verbatim in `6mUScq-6U3U`
— one of the two videos with the most baselines and the fixture that rule is most often
demonstrated on. Every run of it scored 100% recall on a term the prompt handed over.

This is a repo-level check, not a report gate: it runs against source files a human edits,
so error severity is safe. Nothing generates SKILL.md under time pressure, so there is no
incentive to satisfy it with a magic word.

Usage:  uv run scripts/check-fixture-independence.py [--corpus DIR ...]

Exit 0 clean, 2 on a collision, 1 on a usage error.
"""

import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# The instruction files a run reads. Add to this list, never remove from it.
INSTRUCTIONS = [
    "skills/analysis/bullshit-detector/SKILL.md",
    "skills/analysis/bullshit-detector/RUBRIC.md",
    "skills/analysis/bullshit-detector/RUN-RECORD.md",
]

# Where measurable content lives: published reports quote their sources, and the fetch
# cache holds raw transcripts. Both count — a phrase in either is a phrase a run can see.
# Globs are per-directory: recurse the repo's own examples, but only pick up cached
# transcripts from the shared temp dir. Recursing /tmp matches every scratch file on the
# machine and drowns the real signal.
DEFAULT_CORPUS = [
    (REPO / "examples", ["**/*.md"]),
    (REPO / "eval" / "cases", ["**/transcript.md"]),
    (pathlib.Path("/tmp"), ["bs-source-*.md"]),
]

# A quoted span short enough to be a coincidence is not evidence of a leak. Four words
# is the floor at which "consistency builds algorithm authority" stops being an accident.
MIN_WORDS = 4

QUOTED = re.compile(r'"([^"\n]{12,200})"')

# Phrases that are quoted in the instructions but are deliberately generic vocabulary
# rather than worked examples. Keep this list short and justify every entry.
ALLOW = {
    "use your web search tool",
    "widely reported",
    "every outlet covered it",
    "nothing found",
    "no record found",
    "not rateable",
    "arithmetic checks out",
    "the platform's own figure",
    "paid for and produced by",
    "sponsored content",
    "in partnership with",
    # Rubric vocabulary that reports quote *back* at us. The leak this check exists to
    # catch runs the other way — instructions quoting content — and these are the
    # false-positive direction.
    "a source about itself",
    "the same ideal client",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()


def norm_ws(s: str) -> str:
    return " ".join(norm(s).split())


def corpus_files(pairs):
    seen = []
    for d, globs in pairs:
        d = pathlib.Path(d)
        if not d.is_dir():
            continue
        for g in globs:
            for p in d.glob(g):
                if p.is_file() and p not in seen:
                    seen.append(p)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", action="append", default=None,
                    help="directory of measurable content, recursed for *.md (repeatable)")
    args = ap.parse_args()

    pairs = [(d, ["**/*.md"]) for d in args.corpus] if args.corpus else DEFAULT_CORPUS
    files = corpus_files(pairs)
    if not files:
        print("no corpus files found — nothing to check against, which is not a pass",
              file=sys.stderr)
        return 1

    haystacks = {}
    for p in files:
        try:
            haystacks[p] = norm_ws(p.read_text(errors="ignore"))
        except OSError:
            continue

    collisions = []
    checked = 0
    for rel in INSTRUCTIONS:
        path = REPO / rel
        if not path.exists():
            continue
        text = path.read_text()
        for m in QUOTED.finditer(text):
            phrase = m.group(1)
            n = norm_ws(phrase)
            if len(n.split()) < MIN_WORDS or n in ALLOW:
                continue
            checked += 1
            line = text[: m.start()].count("\n") + 1
            for p, hay in haystacks.items():
                if n in hay:
                    collisions.append((rel, line, phrase, p))
                    break

    print(f"checked {checked} quoted spans in {len(INSTRUCTIONS)} instruction files "
          f"against {len(haystacks)} corpus files")

    if collisions:
        print("\nFAIL: worked examples are quoted from content this tool is measured on.\n")
        for rel, line, phrase, p in collisions:
            print(f"  {rel}:{line}")
            print(f"    example : \"{phrase[:90]}\"")
            print(f"    appears : {p}")
            print("    -> replace the example with an invented one, or drop the fixture "
                  "from the measurement set for this rule.\n")
        return 2

    print("✔ no worked example appears in the measurable corpus")
    return 0


if __name__ == "__main__":
    sys.exit(main())
