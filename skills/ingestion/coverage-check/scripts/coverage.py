#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
# ]
# ///
"""Measure how many *independent origins* are behind news coverage of a claim.

Ten URLs are not ten sources. This queries GDELT for articles matching a claim,
then collapses them: same story reprinted across syndication partners groups into
one origin, so the detector can count origins instead of links.

Usage:
    uv run coverage.py "<query>" [--timespan 3m] [--max 250] [--json]

Query supports GDELT operators: "exact phrase", (a OR b), -exclude,
domain:example.com, sourcelang:english.

Output: markdown summary (or --json) on stdout.
Errors: non-zero exit, actionable message on stderr.

Limits worth knowing before you trust the number:
  - GDELT DOC 2.0 covers a ROLLING 3-MONTH WINDOW only. Older claims return
    nothing, and "no coverage" then means "not in the window", not "unreported".
  - Rate limit is roughly one request every 5 seconds. This script backs off and
    retries rather than hammering.
  - GDELT indexes online news. Absence is not evidence; presence is not credibility.
"""

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

API = "https://api.gdeltproject.org/api/v2/doc/doc"
UA = "bullshit-detector/0.5 (+https://github.com/SerhiiKorniienko/bullshit-detector)"

# Two titles match if EITHER measure clears its bar. Both are needed: sequence ratio
# catches reworded-but-similarly-ordered headlines, token overlap catches the same facts
# in a different order ("PNB partners with A.P." vs "Andhra Pradesh, PNB sign MoU").
# Tuned against real GDELT output — at these values, every pair that cleared the bar was
# genuinely the same story, and 0.72 sequence-only missed two wire stories out of three.
TITLE_MATCH = 0.55
TOKEN_MATCH = 0.45
# Articles this close together count as one publication burst.
BURST_HOURS = 24

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "as", "at", "by", "from", "is", "are", "was", "were", "be", "been", "it",
    "its", "this", "that", "these", "those", "will", "says", "say", "said",
    "new", "how", "why", "what", "after", "amid", "over", "into",
}


def fail(msg: str, hint: str = "") -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    if hint:
        print(f"HINT: {hint}", file=sys.stderr)
    sys.exit(1)


def query_gdelt(query: str, timespan: str, maxrecords: int, sort: str, timeout: int) -> list:
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "timespan": timespan,
        "maxrecords": str(maxrecords),
        "sort": sort,
    }
    # Observed behaviour: once GDELT throttles you it stays cross for a while, and a 6s
    # backoff just burns retries. Start well above the documented 1-req/5s floor.
    delay = 20.0
    last = ""
    for attempt in range(4):
        # GDELT is slow — 15s for a trivial query, far longer for a wide window.
        # Say so, or a normal run looks like a hang and gets killed.
        note = "querying GDELT" if attempt == 0 else f"retrying GDELT (attempt {attempt + 1}/4)"
        print(f"{note}: {timespan} window, up to {maxrecords} records — this can take 30-90s…",
              file=sys.stderr, flush=True)
        started = time.monotonic()
        try:
            r = requests.get(API, params=params, headers={"User-Agent": UA}, timeout=timeout)
        except requests.Timeout:
            fail(f"GDELT did not respond within {timeout}s",
                 "it is slow, not broken. Narrow the search (--timespan 7d), lower --max, "
                 f"or raise --timeout above {timeout}")
        except requests.RequestException as e:
            fail(f"could not reach GDELT: {e}", "check connectivity; the API has no key and no auth")
        print(f"  … responded in {time.monotonic() - started:.1f}s", file=sys.stderr, flush=True)
        if r.status_code == 429 or "Please limit requests" in r.text[:200]:
            last = "rate limited"
            if attempt < 3:
                print(f"  … throttled; waiting {delay:.0f}s", file=sys.stderr, flush=True)
                time.sleep(delay)
                delay *= 2.2
            continue
        if r.status_code != 200:
            fail(f"GDELT returned HTTP {r.status_code}", r.text[:200])
        body = r.text.strip()
        if not body:
            return []
        try:
            return json.loads(body).get("articles", []) or []
        except json.JSONDecodeError:
            # GDELT emits bare text for malformed queries rather than a JSON error.
            fail("GDELT did not return JSON", body[:300])
    # Exit 3 == "measurement unavailable", deliberately distinct from exit 1 (bad input).
    # A caller must never read this as "no coverage found".
    print("ERROR: GDELT is throttling — no measurement available for this claim.", file=sys.stderr)
    print("HINT: GDELT returns this well below its stated 1-req/5s limit when its free endpoint is "
          "busy, regardless of IP or client. It is intermittent — retry in a few minutes.",
          file=sys.stderr)
    print("HINT: THIS IS NOT A RESULT. Do not record it as 'no coverage' or let it move a verdict "
          "in either direction. The claim is simply unmeasured.", file=sys.stderr)
    sys.exit(3)


# Params that identify the *visit*, not the article. Exact names plus the utm_ family —
# stripping by prefix beyond utm_ would eat real routing params ("referrer=chapter2").
TRACKING_PARAMS = {"fbclid", "gclid", "ref", "source", "cmpid", "ito", "ocid"}

# Wire-service attributions as they appear in headlines — "(Reuters)", "- Associated
# Press". Title-level only: GDELT returns no article bodies, so the body-head signature
# from #30 is out of reach here, and this weaker tell is labelled as what it is.
WIRE_MARKERS = ("prnewswire", "pr newswire", "business wire", "businesswire",
                "globe newswire", "globenewswire", "(reuters)", "(ap)",
                "associated press", "accesswire", "newsfile corp")


def canonical_url(u: str) -> str:
    """One article, one key: `example.com/x` and `example.com/x?utm_source=twitter`
    were counted as two URLs before this. Lowercase host, drop www and the fragment,
    strip tracking params, sort what survives, trim the trailing slash."""
    try:
        scheme, netloc, path, query, _ = urlsplit((u or "").strip())
    except ValueError:
        return (u or "").strip().lower()
    netloc = netloc.lower().removeprefix("www.")
    kept = sorted((k, v) for k, v in parse_qsl(query, keep_blank_values=True)
                  if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS)
    return urlunsplit(("https", netloc, path.rstrip("/"), urlencode(kept), ""))


def collapse_urls(articles: list) -> tuple:
    """Dedupe articles whose URLs canonicalise to the same key, keeping the first in
    input order (earliest under the default dateasc sort). Mirrors and re-tagged
    shares collide; distinct pages do not. An article with no URL is always kept —
    collapsing the URL-less onto each other would invent syndication out of a data
    gap, which is the one direction this whole file promises never to err in."""
    seen, kept, collapsed = set(), [], 0
    for a in articles:
        if not (a.get("url") or "").strip():
            kept.append(a)
            continue
        key = canonical_url(a["url"])
        if key in seen:
            collapsed += 1
            continue
        seen.add(key)
        kept.append(a)
    return kept, collapsed


def wire_attributed(title: str) -> bool:
    t = (title or "").lower()
    return any(m in t for m in WIRE_MARKERS)


def norm_title(t: str) -> str:
    t = re.sub(r"[^\w\s]", " ", (t or "").lower())
    words = [w for w in t.split() if w not in STOPWORDS and len(w) > 2]
    return " ".join(words)


def parse_seen(s: str):
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return None


def root_domain(d: str) -> str:
    """Strip subdomains so edition.cnn.com and cnn.com are one outlet."""
    d = (d or "").lower().strip()
    d = d.removeprefix("www.")
    parts = d.split(".")
    if len(parts) <= 2:
        return d
    # Handle co.uk, com.au and friends.
    if parts[-2] in ("co", "com", "org", "net", "gov", "ac") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def same_story(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if SequenceMatcher(None, a, b).ratio() >= TITLE_MATCH:
        return True
    A, B = set(a.split()), set(b.split())
    union = A | B
    return bool(union) and len(A & B) / len(union) >= TOKEN_MATCH


def cluster_stories(articles: list) -> list:
    """Group articles into stories by connected components over title similarity.

    Transitivity matters: three outlets covering one wire story can have A~B and B~C
    while A and C score below the bar. Greedy key-matching would split them; union-find
    keeps them together. Observed in real data on a three-outlet Bitcoin story.
    """
    titles = [norm_title(a.get("title", "")) for a in articles]
    parent = list(range(len(articles)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            if same_story(titles[i], titles[j]):
                union(i, j)

    groups = defaultdict(list)
    for idx, art in enumerate(articles):
        groups[find(idx)].append(art)

    clusters = [{"key": titles[root], "items": items} for root, items in groups.items()]
    clusters.sort(key=lambda c: len(c["items"]), reverse=True)
    return clusters


def burst_span(items: list):
    dates = sorted(d for d in (parse_seen(a.get("seendate", "")) for a in items) if d)
    if not dates:
        return None, None, None
    return dates[0], dates[-1], dates[-1] - dates[0]


def analyse(articles: list) -> dict:
    articles, url_dupes = collapse_urls(articles)
    clusters = cluster_stories(articles)
    domains = Counter(root_domain(a.get("domain", "")) for a in articles if a.get("domain"))
    countries = Counter(a.get("sourcecountry") or "unknown" for a in articles)

    out_clusters = []
    for c in clusters:
        items = c["items"]
        doms = sorted({root_domain(a.get("domain", "")) for a in items if a.get("domain")})
        first, last, span = burst_span(items)
        out_clusters.append({
            "headline": items[0].get("title", "").strip(),
            "articles": len(items),
            "domains": doms,
            "distinct_domains": len(doms),
            "wire_attributed": any(wire_attributed(a.get("title", "")) for a in items),
            "first_seen": first.isoformat() if first else None,
            "last_seen": last.isoformat() if last else None,
            # `span` can legitimately be timedelta(0) — simultaneous publication, the
            # strongest syndication signal there is. Test `is not None`, never truthiness.
            "span_hours": round(span.total_seconds() / 3600, 1) if span is not None else None,
            "syndicated": (len(doms) > 1 and span is not None
                           and span <= timedelta(hours=BURST_HOURS)),
        })

    first, last, span = burst_span(articles)
    return {
        "articles": len(articles),
        "url_duplicates_collapsed": url_dupes,
        "distinct_domains": len(domains),
        "story_clusters": len(clusters),
        "first_seen": first.isoformat() if first else None,
        "last_seen": last.isoformat() if last else None,
        "span_hours": round(span.total_seconds() / 3600, 1) if span is not None else None,
        "top_domains": domains.most_common(15),
        "countries": countries.most_common(8),
        "clusters": out_clusters,
    }


def plural(n: int, one: str, many: str = "") -> str:
    return f"{n} {one}" if n == 1 else f"{n} {many or one + 's'}"


def verdict_line(a: dict) -> str:
    """The one sentence the detector actually needs."""
    if a["articles"] == 0:
        return ("No coverage in GDELT's 3-month window. This is NOT evidence the claim is false or "
                "unreported — it may predate the window or fall outside indexed news.")
    syn = [c for c in a["clusters"] if c["syndicated"]]
    if a["story_clusters"] == 1 and a["distinct_domains"] > 1:
        return (f"{a['articles']} articles across {a['distinct_domains']} outlets, but ONE story cluster — "
                f"treat as **1 origin**, not {a['distinct_domains']} independent confirmations.")
    head = (f"{plural(a['articles'], 'article')}, {plural(a['distinct_domains'], 'outlet')}, "
            f"{plural(a['story_clusters'], 'distinct story cluster')}")
    if syn:
        verb = "shows" if len(syn) == 1 else "show"
        return (f"{head} — {len(syn)} of them {verb} syndication (multiple outlets inside "
                f"{BURST_HOURS}h). Count origins, not links.")
    if a["articles"] == 1:
        return f"{head} — a single article. Nothing to corroborate; this is one source, not coverage."
    spread = f" spread over {a['span_hours']}h" if a["span_hours"] is not None else ""
    return (f"{head}{spread} — coverage looks independently developed, "
            f"but confirm the clusters do not share one cited document.")


def render(query: str, a: dict) -> str:
    L = [f"# Coverage check: {query}", "", verdict_line(a), ""]
    if a.get("truncated"):
        L += ["> ⚠️ **Result set hit the `--max` cap, so these counts are lower bounds.** There is more "
              "coverage than shown. Narrow `--timespan` to get a complete picture of a shorter period "
              "rather than a truncated view of a long one.", ""]
    L += [
        "| Metric | Value |",
        "|---|---|",
        f"| Articles matched | {a['articles']} |",
        *([f"| Duplicate URLs collapsed | {a['url_duplicates_collapsed']} |"]
          if a["url_duplicates_collapsed"] else []),
        f"| Distinct outlets | {a['distinct_domains']} |",
        f"| Distinct story clusters | {a['story_clusters']} |",
        f"| First seen | {a['first_seen'] or 'n/a'} |",
        f"| Last seen | {a['last_seen'] or 'n/a'} |",
        f"| Span (hours) | {a['span_hours'] if a['span_hours'] is not None else 'n/a'} |",
        "",
    ]
    if a["clusters"]:
        L += ["## Story clusters", ""]
        for i, c in enumerate(a["clusters"][:10], 1):
            flag = " ⚠️ syndicated" if c["syndicated"] else ""
            if c.get("wire_attributed"):
                flag += " · wire-attributed headline"
            # "all within 0.0h" is noise for a lone article — there is no window to speak of.
            window = (f", all within {c['span_hours']}h"
                      if c["span_hours"] is not None and c["articles"] > 1 else "")
            L.append(f"**{i}. {c['headline']}**{flag}")
            L.append(f"- {plural(c['articles'], 'article')} across "
                     f"{plural(c['distinct_domains'], 'outlet')}{window}")
            L.append(f"- {', '.join(c['domains'][:12])}")
            L.append("")
    if a["top_domains"]:
        L += ["## Outlets", "", ", ".join(f"{d} ({n})" for d, n in a["top_domains"]), ""]
    L += [
        "---",
        "*GDELT DOC 2.0, rolling 3-month window, matched against full article text rather than "
        "headlines. Absence is not evidence of absence. Clustering groups reprints, rewritten wire "
        "copy and reordered headlines; two newsrooms that independently reached the same finding in "
        "genuinely different words stay separate, so syndication is under-reported, never invented.*",
    ]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Count independent origins behind news coverage of a claim")
    ap.add_argument("query", help='search terms; GDELT operators allowed ("exact phrase", a OR b, -not)')
    ap.add_argument("--timespan", default="3m", help="lookback window: 15min, 1h, 7d, 4w, 3m (default: 3m)")
    ap.add_argument("--max", type=int, default=250, dest="maxrecords", help="max articles, up to 250")
    ap.add_argument("--sort", default="dateasc", choices=["dateasc", "datedesc", "hybridrel"],
                    help="dateasc (default) surfaces earliest coverage, which is what origin analysis wants")
    ap.add_argument("--timeout", type=int, default=120, help="seconds to wait for GDELT (default: 120)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = ap.parse_args()

    if not args.query.strip():
        fail("empty query")
    if not 1 <= args.maxrecords <= 250:
        fail("--max must be between 1 and 250", "GDELT caps artlist results at 250")

    articles = query_gdelt(args.query.strip(), args.timespan, args.maxrecords, args.sort, args.timeout)
    a = analyse(articles)
    # Hitting the cap means the result set is cut off, so every count below is a LOWER BOUND.
    a["truncated"] = len(articles) >= args.maxrecords

    if args.json:
        print(json.dumps({"query": args.query, "verdict": verdict_line(a), **a}, ensure_ascii=False, indent=2))
    else:
        print(render(args.query, a))


if __name__ == "__main__":
    main()
