# The claims file — `bullshit-detector/claim@1`

Written beside every report: same path, `.md` swapped for `.claims.jsonl`. **One JSON object per
line**, one line per claim.

**Read this file only when you are writing the claims file.** Like the run record, it is off the
runtime path of a report that does not use it.

```json
{"schema":"bullshit-detector/claim@1","n":"6","section":"load_bearing","type":"factual",
 "claim":"Microsoft, Google, Amazon and Meta spent [$376 billion] on AI infrastructure in 2025 [06:45]",
 "quote":"376 billion dollars",
 "verdict":"plausible","unverifiable_kind":null,
 "sources":[{"url":"https://example.com/report","tier":2},{"url":"https://example.org/coverage","tier":3}],
 "origin_count":2,"origin_kind":"judged","derived_from":null,"readings":null,
 "evidence":"Guidance late in the year was \"more than $380 billion\"; retrospective coverage uses a higher figure. $376B sits below both — likely an earlier guidance number rather than the final actual."}
```

## Why one line per claim

A truncated 40-claim JSON *object* costs the whole run. A truncated JSONL file costs the last
claim. Anything reading this file must therefore parse **line by line, skipping and reporting bad
lines** — never `json.loads()` the whole file. `tally.py --compose` does exactly that; a parser
that crashes on one bad line has given up the only durability this format buys.

**Write each line as its claim resolves**, not batched at the end. A file written in one flush at
the end has the same failure mode as the in-context table it replaced, and the same failure mode
the query log already warns about: a list rebuilt from memory is wrong in the direction that
flatters the run.

## Fields

| field | type | required |
|---|---|---|
| `schema` | `"bullshit-detector/claim@1"` | always |
| `n` | string — `"6"`, `"6a"` | always |
| `section` | `load_bearing` \| `incidental` | always |
| `type` | `factual` \| `prediction` \| `opinion` \| `anecdote` | always |
| `claim` | string, decontextualized, brackets and timestamp inline | always |
| `quote` | string \| null — the verbatim span from the source | factual/anecdote rows |
| `verdict` | `confirmed` \| `plausible` \| `misleading` \| `false` \| `unverifiable` \| `not checked` \| null | null **only** for opinion/prediction |
| `unverifiable_kind` | `searched` \| `by_construction` \| null | iff `verdict` is `unverifiable` |
| `sources` | array of `{url, tier: 1-5}` | ≥1 unless not-checked, unverifiable-by-construction, or derived |
| `origin_count` | int \| null | iff more than one source |
| `origin_kind` | `measured` \| `judged` \| null | iff `origin_count` is set |
| `derived_from` | string \| null — the `n` of the row this rests on | derived rows |
| `readings` | array of `{basis, note}` \| null — ≥2 entries | rows kept under every reading |
| `evidence` | string | whenever a search happened |

**`n` is a string, not an integer.** Split-late suffixes (`6a`, `6b`) are the native case, not a
special one — see RUBRIC on why a row splits rather than the table renumbering beneath it.

**`quote` is a field, not a convention.** It used to be inferred by looking for `"…"` spans inside
the claim text, which cannot distinguish a verbatim quote from the report's own phrasing in
quotation marks — RUBRIC names that as the most common way the quote check is failed. A field
carries the assertion "this is verbatim" unambiguously. It does not stop anyone getting the quote
wrong; `tally.py` still checks it against the cached source.

**`evidence` stays prose, deliberately.** Shown sums, carried ranges, named measurement bases and
tier caveats are claim-specific reasoning over heterogeneous arithmetic. A typed sub-schema for
them would buy no enforcement — a script still cannot confirm the arithmetic is *right* without
re-deriving it from the source — while making the file materially harder to write.

## What reads it

`tally.py --compose` renders the claims tables, then counts the rendered rows **with the same
`scan()` the gate uses**, so the tally line cannot disagree with the table above it. That is the
point of the format: today the same quantity is parsed out of prose three times — by the gate, by
the renderer, and by hand — and the three disagreed on a published page.
