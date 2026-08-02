#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Where a run's wall clock actually goes, measured from the harness transcript.

Usage:
    uv run scripts/runprofile.py --discover              # every detector run on this machine
    uv run scripts/runprofile.py <transcript.jsonl> ...  # specific ones
    uv run scripts/runprofile.py --discover --rollup     # medians across runs
    uv run scripts/runprofile.py --discover --json       # machine-readable

This is a development tool, and a deliberately different kind of number from
`runstats.py`. That one reads the run records, which the agent writes about its own
behaviour; nothing recounts them. This one reads the harness transcript — timestamps
the agent never sees and cannot round in its own favour — so a phase split from here
is a measurement rather than a self-report.

Why it exists: a run's wall split was known only from one run's self-report
(verification ~25%, writing ~44%, extraction/setup ~25%, gate ~6%). Optimising
against an n=1 self-report is how three hypotheses got named and killed in one day.

What a transcript gives us, per entry: a millisecond `timestamp`, the tool call or
content block it carries, and (on assistant entries) the API `usage` block. From that:

  model time  = gap from the previous event to the end of an assistant content block.
                Includes queue, prefill and decode; the transcript cannot separate them.
  tool  time  = tool_result timestamp - tool_use timestamp.
  idle  time  = gap from an assistant message ending to the next human prompt.
                Zero in subagent runs, nonzero in interactive ones. Excluded from
                the phase table and reported separately, or a human making coffee
                lands in whatever phase was open.

ATTRIBUTION RULE, and it is a choice: a thinking or text block is charged to the
phase of the *next* tool call, not the previous one. Deliberation is charged to what
it produced — the two minutes of thinking before the report gets written are report
writing, not verification. Blocks after the last tool call go to `wrapup`.

Token counts come from `usage`, and the trap there is that the per-block `usage` is a
*streaming snapshot*, not that block's cost: a message's thinking block reports 3
output tokens and its final block reports 1,065 for the same message. So tokens are
taken as the maximum over a message's blocks and charged to the phase of its last
block. Summing per block would multiply the total; taking the first would divide it.

Thinking *text* is not persisted in the transcript (the field is empty next to its
signature), so there is no way to split a message's output tokens into thinking and
answer. Thinking is therefore measured in seconds, which is the number that matters
here anyway.

Overlapping tool calls (a message that fires four subagents at once) are unioned, not
summed — otherwise a parallel run reports more wall time than it took, which is the
exact mistake this tool exists to prevent.
"""

import argparse
import glob
import json
import os
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

# Phases in workflow order. `instructions` and `source-reread` are split out of setup
# on purpose: "how much does reading the prompt cost" has been asserted three times
# and measured never.
PHASES = [
    "setup",          # before the content arrives: skill load, date, tool search
    "instructions",   # reading SKILL.md / RUBRIC.md / RUN-RECORD.md
    "fetch",          # getting the content
    "extract",        # reading it and building the claims list
    "verify",         # searching
    "source-reread",  # re-reading the cached source mid-run
    "compose",        # writing the report file
    "gate",           # tally.py, retraction check, and the edits they force
    "render",         # render_report.py / report-card
    "wrapup",         # the handoff after the artifact exists
]

REPORT_RE = re.compile(r"bs-report-[\w.-]+\.md\b")
SOURCE_RE = re.compile(r"bs-source-[\w.-]+\.md\b")


def child_index() -> dict:
    """Map a parent's Agent tool_use id to the child agent's transcript.

    A delegated run does its searching in a different file. Without this, a run that
    farmed verification out to four subagents reads as zero searches and 22 minutes
    of unexplained tool time — which is how the parallel experiment's real shape
    stayed invisible.
    """
    idx = {}
    for meta in glob.glob(str(Path.home() / ".claude" / "projects" / "*" / "*"
                              / "subagents" / "*.meta.json")):
        try:
            d = json.loads(Path(meta).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("toolUseId"):
            idx[d["toolUseId"]] = Path(meta.replace(".meta.json", ".jsonl"))
    return idx


CHILDREN = {}


def child_summary(tool_id: str) -> dict:
    """What a delegated agent actually did, so its time can be labelled."""
    path = CHILDREN.get(tool_id)
    if not path or not path.exists():
        return {}
    try:
        entries = load_entries(path)
    except OSError:
        return {}
    searches = fetches = 0
    for d in entries:
        if d["type"] != "assistant":
            continue
        for b in (d.get("message") or {}).get("content") or []:
            if b.get("type") == "tool_use":
                if b.get("name") == "WebSearch":
                    searches += 1
                elif b.get("name") == "WebFetch":
                    fetches += 1
    return {"searches": searches, "fetches": fetches}


def parse_ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def default_transcript_globs() -> list:
    root = Path.home() / ".claude" / "projects"
    return [
        str(root / "*" / "*.jsonl"),
        str(root / "*" / "*" / "subagents" / "*.jsonl"),
    ]


# --------------------------------------------------------------------------- parse


def load_entries(path: Path) -> list:
    out = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") in ("assistant", "user") and d.get("timestamp"):
                out.append(d)
    out.sort(key=lambda d: d["timestamp"])
    return out


def build_events(entries: list) -> list:
    """One flat, ordered event stream.

    kinds: 'block' (an assistant content block), 'tool_result', 'prompt' (a human turn).
    """
    events = []
    for d in entries:
        ts = parse_ts(d["timestamp"])
        msg = d.get("message") or {}
        content = msg.get("content")
        if d["type"] == "assistant":
            blocks = content if isinstance(content, list) else []
            for b in blocks:
                ev = {
                    "ts": ts,
                    "kind": "block",
                    "block": b.get("type"),
                    "msg_id": msg.get("id"),
                    "usage": msg.get("usage") or {},
                    "model": msg.get("model"),
                    "effort": d.get("effort"),
                    "chars": 0,
                }
                if b.get("type") == "thinking":
                    ev["chars"] = len(b.get("thinking") or "")
                elif b.get("type") == "text":
                    ev["chars"] = len(b.get("text") or "")
                elif b.get("type") == "tool_use":
                    ev["tool"] = b.get("name")
                    ev["input"] = b.get("input") or {}
                    ev["tool_id"] = b.get("id")
                    ev["chars"] = len(json.dumps(ev["input"]))
                events.append(ev)
        else:
            blocks = content if isinstance(content, list) else []
            results = [b for b in blocks if b.get("type") == "tool_result"]
            if results:
                for b in results:
                    body = b.get("content")
                    if isinstance(body, list):
                        body = " ".join(str(x.get("text", "")) for x in body
                                        if isinstance(x, dict))
                    body = str(body)
                    events.append({
                        "ts": ts, "kind": "tool_result",
                        "tool_id": b.get("tool_use_id"),
                        "chars": len(body),
                        # Kept so gate verdicts can be read back out of the run.
                        "text": body[:6000],
                    })
            elif not d.get("isMeta"):
                events.append({"ts": ts, "kind": "prompt",
                               "text": json.dumps(content)[:4000]})
    events.sort(key=lambda e: e["ts"])
    return events


# ----------------------------------------------------------------------- run split


def find_runs(events: list) -> list:
    """Slice the stream into runs, anchored on the report file being written.

    A run is the span from the human turn (or transcript start) that precedes its
    first detector marker, through the last gate/render call that follows its report
    write, plus the one assistant message after it (the handoff).
    """
    anchors = [i for i, e in enumerate(events)
               if e["kind"] == "block" and e.get("tool") in ("Write", "Edit", "MultiEdit")
               and REPORT_RE.search(json.dumps(e.get("input", {}))[:2000])]
    if not anchors:
        return []
    # Collapse anchors belonging to one report (first Write, then gate-forced edits).
    runs, cur = [], [anchors[0]]
    for a in anchors[1:]:
        same = REPORT_RE.search(json.dumps(events[a]["input"])[:2000])
        prev = REPORT_RE.search(json.dumps(events[cur[-1]]["input"])[:2000])
        if same and prev and same.group(0) == prev.group(0):
            cur.append(a)
        else:
            runs.append(cur)
            cur = [a]
    runs.append(cur)

    out = []
    prev_end = 0
    for group in runs:
        first, last = group[0], group[-1]
        start = min(prev_end, first)
        for i in range(first, start - 1, -1):
            if events[i]["kind"] == "prompt":
                start = i
                break
        # The run owns everything after its report write until the human speaks again:
        # the gate, the edits it forces, the render, and the handoff message.
        end = len(events) - 1
        for i in range(last + 1, len(events)):
            if events[i]["kind"] == "prompt":
                end = i - 1
                break
        out.append((start, end))
        prev_end = end + 1
    return out


# ------------------------------------------------------------------- classification


def classify_tool(tool: str, inp: dict, state: str, seen_search: bool,
                  tool_id: str = "") -> str:
    blob = json.dumps(inp)[:4000]
    path = str(inp.get("file_path") or inp.get("path") or inp.get("notebook_path") or "")
    cmd = str(inp.get("command") or "")

    if tool == "Skill":
        name = str(inp.get("skill") or "")
        if "fetch-content" in name:
            return "fetch"
        if "report-card" in name:
            return "render"
        if "bullshit-detector" in name:
            return "instructions"
        return "setup"
    if tool == "Bash":
        if "fetch.py" in cmd:
            return "fetch"
        if "tally.py" in cmd or "retractions.py" in cmd:
            return "gate"
        if "render_report" in cmd or "render_carousel" in cmd:
            return "render"
        if "coverage.py" in cmd:
            return "verify"
        if SOURCE_RE.search(cmd) and not seen_search:
            return "fetch"
        if re.search(r"\b(date|pwd|ls|mkdir|env|which|cat .*SKILL)\b", cmd) and not seen_search:
            return "setup"
        return state
    if tool in ("WebSearch",):
        return "verify"
    if tool == "WebFetch":
        return "verify" if seen_search else "fetch"
    if tool == "Read":
        if re.search(r"(SKILL|RUBRIC|RUN-RECORD|CLAUDE|README)\.md", path):
            return "instructions"
        if SOURCE_RE.search(path):
            return "fetch" if not seen_search else "source-reread"
        if REPORT_RE.search(path):
            return "gate"
        return state
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        if REPORT_RE.search(path) or REPORT_RE.search(blob):
            # Rework only counts as rework once something has judged the draft.
            # A report built in three Writes before the gate ever ran is still
            # being written.
            return "gate" if state in ("gate", "render", "wrapup") else "compose"
        if SOURCE_RE.search(path):
            return "fetch"
        return state
    if tool in ("ToolSearch", "Glob", "Grep"):
        return "setup" if not seen_search else state
    if tool in ("Agent", "Task"):
        kid = child_summary(tool_id)
        if kid.get("searches"):
            return "verify"
        return "verify" if seen_search else state
    return state


def phase_of_blocks(events: list, lo: int, hi: int) -> list:
    """Assign a phase to every event in [lo, hi]. Two passes: tools first, then
    deliberation charged forward to the tool it produced."""
    phases = [None] * (hi - lo + 1)
    state = "setup"
    seen_search = False
    report_written = False
    gate_ruled = False
    for i in range(lo, hi + 1):
        e = events[i]
        if e["kind"] != "block" or not e.get("tool"):
            continue
        ph = classify_tool(e["tool"], e.get("input", {}), state, seen_search,
                           e.get("tool_id", ""))
        if e["tool"] in ("WebSearch",) or (e["tool"] == "Bash" and "coverage.py" in str(e.get("input", {}).get("command", ""))):
            seen_search = True
        if ph == "compose":
            if gate_ruled:
                ph = "gate"           # a redraft the gate asked for
            else:
                report_written = True
        # A tally run before the report exists is the agent looking the tool up, not
        # the gate ruling on a draft. Only the latter turns later edits into rework.
        if ph == "gate" and e["tool"] == "Bash" and report_written:
            gate_ruled = True
        phases[i - lo] = ph
        # State advances on the workflow-moving phases only; a Read of the rubric
        # mid-verification must not rewind the run to `instructions`.
        if ph in ("fetch", "verify", "compose", "gate", "render"):
            state = ph
        elif ph == "setup" and state == "setup":
            state = "setup"
        if ph == "fetch":
            state = "extract"   # once the text is in hand we are reading it
        if ph == "verify":
            state = "verify"
    # Deliberation -> next tool's phase; trailing blocks -> wrapup.
    nxt = "wrapup"
    for i in range(hi, lo - 1, -1):
        if phases[i - lo] is not None:
            nxt = phases[i - lo]
        else:
            phases[i - lo] = nxt
    return phases


# ---------------------------------------------------------------------- profiling


def profile(events: list, lo: int, hi: int, label: str) -> dict:
    phases = phase_of_blocks(events, lo, hi)
    result_ts = {e["tool_id"]: e["ts"] for e in events[lo:hi + 1]
                 if e["kind"] == "tool_result" and e.get("tool_id")}

    z = lambda: {p: 0.0 for p in PHASES}
    wall, model, tool_t, thinking = z(), z(), z(), z()
    out_tok, cc_tok, cr_tok = z(), z(), z()
    calls = {p: 0 for p in PHASES}
    tools = {}
    biggest = []
    idle = 0.0
    delegated = {"agents": 0, "searches": 0}
    models, efforts = {}, {}
    intervals = []          # (start, end, phase) for every tool call
    msg_usage = {}          # msg_id -> (max usage, phase of its last block)

    prev_ts = events[lo]["ts"]
    for i in range(lo, hi + 1):
        e = events[i]
        ph = phases[i - lo] or "wrapup"
        gap = max(0.0, e["ts"] - prev_ts)

        if e["kind"] == "block":
            model[ph] += gap
            if e["block"] == "thinking":
                thinking[ph] += gap
            biggest.append((gap, ph, e["block"], e.get("tool") or "", e.get("chars", 0)))
            if e.get("model"):
                models[e["model"]] = models.get(e["model"], 0) + 1
            if e.get("effort"):
                efforts[e["effort"]] = efforts.get(e["effort"], 0) + 1
            mid = e.get("msg_id")
            if mid:
                u = e.get("usage") or {}
                prev = msg_usage.get(mid, ({}, ph))[0]
                best = u if u.get("output_tokens", 0) >= prev.get("output_tokens", 0) else prev
                msg_usage[mid] = (best, ph)
            if e.get("tool"):
                calls[ph] += 1
                if e["tool"] in ("Agent", "Task"):
                    kid = child_summary(e.get("tool_id", ""))
                    delegated["agents"] += 1
                    delegated["searches"] += kid.get("searches", 0)
                end = result_ts.get(e.get("tool_id"))
                if end:
                    d = max(0.0, end - e["ts"])
                    intervals.append((e["ts"], end, ph))
                    t = tools.setdefault(e["tool"], {"n": 0, "sec": 0.0, "each": []})
                    t["n"] += 1
                    t["sec"] += d
                    t["each"].append(d)
                else:
                    t = tools.setdefault(e["tool"], {"n": 0, "sec": 0.0, "each": []})
                    t["n"] += 1
        elif e["kind"] == "prompt":
            idle += gap
        prev_ts = max(prev_ts, e["ts"])
        if e["kind"] == "block" and e.get("tool"):
            prev_ts = max(prev_ts, result_ts.get(e.get("tool_id"), e["ts"]))

    # Tool wall as a union: four subagents running at once cost one stretch of clock,
    # not four. Each stretch is charged to the phase of the call that opened it.
    cursor = 0.0
    for start, end, ph in sorted(intervals):
        eff = max(0.0, end - max(start, cursor))
        tool_t[ph] += eff
        cursor = max(cursor, end)

    for u, ph in msg_usage.values():
        out_tok[ph] += u.get("output_tokens", 0)
        cc_tok[ph] += u.get("cache_creation_input_tokens", 0)
        cr_tok[ph] += u.get("cache_read_input_tokens", 0)

    for p in PHASES:
        wall[p] = model[p] + tool_t[p]
    total = sum(wall.values())
    biggest.sort(reverse=True)
    return {
        "label": label,
        "model_name": max(models, key=models.get) if models else "",
        "effort": max(efforts, key=efforts.get) if efforts else "",
        "searches_measured": tools.get("WebSearch", {}).get("n", 0) + delegated["searches"],
        "delegated": delegated,
        "start": events[lo]["ts"], "end": events[hi]["ts"],
        "wall_seconds": round(total, 1),
        "span_seconds": round(events[hi]["ts"] - events[lo]["ts"], 1),
        "idle_seconds": round(idle, 1),
        "model_seconds": round(sum(model.values()), 1),
        "tool_seconds": round(sum(tool_t.values()), 1),
        "thinking_seconds": round(sum(thinking.values()), 1),
        "phases": {p: {"wall": round(wall[p], 1), "pct": round(100 * wall[p] / total, 1) if total else 0.0,
                       "model": round(model[p], 1), "tool": round(tool_t[p], 1),
                       "thinking": round(thinking[p], 1), "calls": calls[p],
                       "out_tokens": out_tok[p], "cache_creation": cc_tok[p],
                       "cache_read": cr_tok[p]} for p in PHASES},
        "tools": {k: {"n": v["n"], "sec": round(v["sec"], 1),
                      "median": round(statistics.median(v["each"]), 1)}
                  for k, v in sorted(tools.items(), key=lambda kv: -kv[1]["sec"])},
        "output_tokens": sum(out_tok.values()),
        "top_blocks": [{"sec": round(g, 1), "phase": p, "block": b, "tool": t, "chars": c}
                       for g, p, b, t, c in biggest[:8]],
        # Every thinking block, so "one long deliberation or a hundred short ones"
        # is answerable without re-parsing.
        "think_blocks": sorted((round(g, 1) for g, p, b, t, c in biggest if b == "thinking"),
                               reverse=True),
    }


# What the gate rejected, split by who can fix it. Bookkeeping is arithmetic the
# script can derive; content is a judgement it cannot. The split is the whole point
# of moving derived numbers out of the model's hands — a run whose only rejections
# are content rejections is a run where the gate is doing its actual job.
BOOKKEEPING_REJECTION = (
    "tally line", "no tally line", "run line", "no run line", "run record",
    "version stamp", "wall time", "per claim", "ambiguous line", "no ambiguous",
)
CONTENT_REJECTION = (
    "nothing to click", "origin count", "not in the source text", "claim numbers",
    "sponsored", "verdict marker", "unverifiable", "no claim rows", "unreachable",
    "quote", "verdict cell", "linked source url", "no verdict at all",
)


def gate_rejections(events: list, lo: int, hi: int) -> dict:
    """Read every gate verdict out of the run and bucket the rejections."""
    calls = {}
    for i in range(lo, hi + 1):
        e = events[i]
        if e["kind"] == "block" and e.get("tool") == "Bash" \
                and "tally.py" in str(e.get("input", {}).get("command", "")):
            calls[e.get("tool_id")] = True
    out = {"invocations": 0, "passes": 0, "failures": 0,
           "bookkeeping": 0, "content": 0, "unclassified": [], "lines": []}
    for i in range(lo, hi + 1):
        e = events[i]
        if e["kind"] != "tool_result" or e.get("tool_id") not in calls:
            continue
        text = e.get("text") or ""
        out["invocations"] += 1
        rejected = [l.strip().lstrip("✗").strip()
                    for l in text.split("\n") if l.strip().startswith("✗")]
        if not rejected:
            out["passes"] += 1
            continue
        out["failures"] += 1
        for line in rejected:
            low = line.lower()
            out["lines"].append(line[:110])
            if any(k in low for k in BOOKKEEPING_REJECTION):
                out["bookkeeping"] += 1
            elif any(k in low for k in CONTENT_REJECTION):
                out["content"] += 1
            else:
                out["unclassified"].append(line[:110])
    return out


def print_timeline(events: list, lo: int, hi: int) -> None:
    """Every event with the phase it was charged to, so the table can be audited.

    A phase split nobody can check line by line is another self-report.
    """
    phases = phase_of_blocks(events, lo, hi)
    result_ts = {e["tool_id"]: e["ts"] for e in events[lo:hi + 1]
                 if e["kind"] == "tool_result" and e.get("tool_id")}
    t0 = events[lo]["ts"]
    prev = t0
    for i in range(lo, hi + 1):
        e = events[i]
        if e["kind"] == "tool_result":
            continue
        ph = phases[i - lo]
        gap = e["ts"] - prev
        dur = ""
        if e.get("tool") and result_ts.get(e.get("tool_id")):
            dur = f" tool {result_ts[e['tool_id']] - e['ts']:.0f}s"
        what = e.get("tool") or e.get("block") or e["kind"]
        detail = ""
        if e.get("tool"):
            inp = e.get("input", {})
            detail = str(inp.get("command") or inp.get("query") or inp.get("file_path")
                         or inp.get("skill") or inp.get("url") or inp.get("description") or "")[:70]
        print(f"  +{e['ts']-t0:7.0f}s  gen {gap:6.0f}s{dur:>10}  {str(ph):<13} {what:<10} {detail}")
        prev = max(prev, e["ts"], result_ts.get(e.get("tool_id"), 0))


def report_paths_of(events: list, lo: int, hi: int) -> list:
    """Every report filename the run wrote, in order.

    Runs that draft to one file and finalise to another are common enough that
    picking the first match names the draft and loses the run record.
    """
    seen = []
    for i in range(lo, hi + 1):
        e = events[i]
        if e["kind"] == "block" and e.get("tool") in ("Write", "Edit", "MultiEdit"):
            m = REPORT_RE.search(json.dumps(e.get("input", {}))[:2000])
            if m and m.group(0) not in seen:
                seen.append(m.group(0))
    return seen


# ------------------------------------------------------------------------- output


def fmt_mmss(sec: float) -> str:
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def print_run(r: dict) -> None:
    print(f"\n=== {r['label']}   [{r.get('model_name','?')} {r.get('effort','')}]")
    print(f"    report: {r.get('report') or '(none)'}"
          + (f"   version {r['version']}" if r.get("version") else "")
          + (f"   N={r['N']} M={r['M']}" if r.get("N") else "")
          + f"   searches(measured)={r['searches_measured']}"
          + (f" via {r['delegated']['agents']} subagents" if r["delegated"]["agents"] else "")
          + (f" reported={r['searches']}" if r.get("searches") is not None else ""))
    print(f"    wall {fmt_mmss(r['wall_seconds'])} ({r['wall_seconds']:.0f}s)"
          f"   model {r['model_seconds']:.0f}s ({100*r['model_seconds']/max(r['wall_seconds'],1):.0f}%)"
          f"   tools {r['tool_seconds']:.0f}s ({100*r['tool_seconds']/max(r['wall_seconds'],1):.0f}%)"
          f"   thinking {r['thinking_seconds']:.0f}s ({100*r['thinking_seconds']/max(r['wall_seconds'],1):.0f}%)"
          f"   human idle {r['idle_seconds']:.0f}s")
    print(f"    {'phase':<14}{'wall':>8}{'%':>7}{'model':>8}{'tools':>8}{'think':>8}{'calls':>7}{'out_tok':>9}")
    for p in PHASES:
        d = r["phases"][p]
        if d["wall"] < 0.05 and d["calls"] == 0:
            continue
        print(f"    {p:<14}{d['wall']:>8.0f}{d['pct']:>7.1f}{d['model']:>8.0f}"
              f"{d['tool']:>8.0f}{d['thinking']:>8.0f}{d['calls']:>7}{d['out_tokens']:>9}")
    tools = ", ".join(f"{k}×{v['n']} {v['sec']:.0f}s(med {v['median']:.1f})"
                      for k, v in list(r["tools"].items())[:6])
    print(f"    tools: {tools}")
    g = r.get("gate") or {}
    if g.get("invocations"):
        print(f"    gate: {g['invocations']} runs, {g['passes']} pass / {g['failures']} fail"
              f"  →  {g['bookkeeping']} bookkeeping, {g['content']} content"
              + (f", {len(g['unclassified'])} unclassified" if g["unclassified"] else ""))
        for line in g["lines"][:4]:
            print(f"      ✗ {line}")
    print("    longest single generations:")
    for b in r["top_blocks"][:5]:
        print(f"      {b['sec']:>6.0f}s  {b['phase']:<13} {b['block']:<9} "
              f"{b['tool']:<10} {b['chars']:>7} chars")


def print_table(runs: list) -> None:
    """One line per run — the shape of the corpus, for spotting confounds.

    The model column is not decoration: main-session runs and blind subagent runs
    are not the same instrument, and a release-over-release comparison that mixes
    them is measuring the harness.
    """
    print(f"{'when':<17}{'model':<8}{'ver':<8}{'wall':>7}{'N':>4}{'M':>4}{'srch':>5}"
          + "".join(f"{p[:5]:>7}" for p in PHASES) + f"{'think':>7}")
    for r in runs:
        d = r["phases"]
        print(f"{datetime.fromtimestamp(r['start']):%m-%d %H:%M}    "
              f"{(r.get('model_name') or '?').replace('claude-','')[:6]:<8}"
              f"{str(r.get('version') or '-'):<8}"
              f"{fmt_mmss(r['wall_seconds']):>7}"
              f"{str(r.get('N') or '-'):>4}{str(r.get('M') or '-'):>4}"
              f"{r['searches_measured']:>5}"
              + "".join(f"{d[p]['pct']:>7.1f}" for p in PHASES)
              + f"{100*r['thinking_seconds']/max(r['wall_seconds'],1):>7.1f}")


def rollup(runs: list) -> None:
    print("\n=== ROLLUP  (median across %d runs)" % len(runs))
    print(f"    {'phase':<14}{'med %':>8}{'min %':>8}{'max %':>8}{'med s':>8}")
    for p in PHASES:
        vals = [r["phases"][p]["pct"] for r in runs]
        secs = [r["phases"][p]["wall"] for r in runs]
        if max(vals) < 0.05:
            continue
        print(f"    {p:<14}{statistics.median(vals):>8.1f}{min(vals):>8.1f}"
              f"{max(vals):>8.1f}{statistics.median(secs):>8.0f}")
    for k, lab in (("model_seconds", "model"), ("tool_seconds", "tools"),
                   ("thinking_seconds", "thinking")):
        pct = [100 * r[k] / max(r["wall_seconds"], 1) for r in runs]
        print(f"    {lab:<14}{statistics.median(pct):>8.1f}{min(pct):>8.1f}{max(pct):>8.1f}")


def attach_run_record(r: dict) -> None:
    """Pair a profiled run with the .run.json it produced, when one exists.

    Candidates are tried newest-written-last first, so a run that drafted to one
    filename and finalised to another is matched on the file it actually shipped.
    """
    roots = [os.environ.get("BULLSHIT_DETECTOR_REPORTS"),
             str(Path.home() / ".bullshit-detector" / "reports"), "/tmp"]
    for name in reversed(r.get("reports") or []):
        for root in roots:
            if not root:
                continue
            for p in glob.glob(str(Path(root).expanduser() / "**" / (name[:-3] + ".run.json")),
                               recursive=True):
                try:
                    d = json.loads(Path(p).read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                r["report"] = name
                r["version"] = d.get("skill_version") or d.get("version")
                claims = d.get("claims") or {}
                r["N"] = claims.get("extracted")
                r["M"] = claims.get("checked")
                r["searches"] = (d.get("queries") if isinstance(d.get("queries"), int)
                                 else len(d.get("queries") or []))
                r["reported_wall"] = d.get("wall_seconds")
                return


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcripts", nargs="*")
    ap.add_argument("--discover", action="store_true",
                    help="scan ~/.claude/projects for transcripts containing runs")
    ap.add_argument("--rollup", action="store_true", help="medians across runs")
    ap.add_argument("--table", action="store_true", help="one line per run")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-wall", type=float, default=120.0,
                    help="ignore fragments shorter than this many seconds")
    ap.add_argument("--timeline", action="store_true",
                    help="print every event with the phase it was charged to")
    ap.add_argument("--loose", action="store_true",
                    help="keep spans that wrote a report without searching or gating")
    args = ap.parse_args()

    paths = [Path(p) for p in args.transcripts]
    if args.discover or not paths:
        for g in default_transcript_globs():
            paths += [Path(p) for p in glob.glob(g)]
    paths = sorted(set(paths))
    CHILDREN.update(child_index())

    runs = []
    for p in paths:
        try:
            entries = load_entries(p)
        except OSError:
            continue
        if not entries:
            continue
        events = build_events(entries)
        if not events:
            continue
        for lo, hi in find_runs(events):
            label = f"{p.parent.name}/{p.name[:8]}  {datetime.fromtimestamp(events[lo]['ts']):%Y-%m-%d %H:%M}"
            r = profile(events, lo, hi, label)
            if r["wall_seconds"] < args.min_wall:
                continue
            # A dev session editing a report file is not a run. A run searches, or
            # at minimum gates what it wrote.
            if not args.loose and r["searches_measured"] < 3 \
                    and r["phases"]["gate"]["calls"] == 0:
                continue
            r["gate"] = gate_rejections(events, lo, hi)
            r["reports"] = report_paths_of(events, lo, hi)
            r["report"] = (r["reports"] or [""])[-1]
            r["transcript"] = str(p)
            attach_run_record(r)
            r["_events"] = (events, lo, hi) if args.timeline else None
            runs.append(r)

    runs.sort(key=lambda r: r["start"])
    if args.json:
        print(json.dumps([{k: v for k, v in r.items() if k != "_events"} for r in runs],
                         indent=1))
        return 0
    if not runs:
        print("no runs found", file=sys.stderr)
        return 1
    if args.table:
        print_table(runs)
        rollup(runs)
        return 0
    for r in runs:
        print_run(r)
        if args.timeline and r.get("_events"):
            print_timeline(*r["_events"])
    if args.rollup or len(runs) > 1:
        rollup(runs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
