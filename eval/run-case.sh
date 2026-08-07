#!/usr/bin/env bash
set -euo pipefail

# Run one eval case end to end — a blind headless run of the full skill against the
# committed transcript, then score it. Costs a real run: 15–25 minutes of wall clock
# and real model spend per case. See eval/README.md for the method rules this encodes.
#
# Usage:  eval/run-case.sh eval/cases/<id> <outdir>
# Env:    EVAL_MODEL (default: the harness default) · EVAL_EFFORT (default xhigh —
#         every baseline on record ran at xhigh; change it only in a deliberate arm)

CASE_DIR=$(cd "$1" && pwd)
OUT=$2
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)

CASE_ID=$(basename "$CASE_DIR")
TRANSCRIPT="$CASE_DIR/transcript.md"
REPORT="$OUT/report-$CASE_ID.md"
SKILL="$HOME/.claude/skills/bullshit-detector"
[ -e "$SKILL" ] || SKILL="$HOME/.agents/skills/bullshit-detector"
[ -e "$SKILL" ] || { echo "no installed skill found — run scripts/link-skills.sh" >&2; exit 1; }
[ -f "$TRANSCRIPT" ] || { echo "no transcript at $TRANSCRIPT" >&2; exit 1; }

# The prompt encodes the method rules that are not optional:
#  - blind: no examples/, no prior reports, no repo spelunking
#  - the installed skill's paths are handed over, so the run measures the tool, not
#    the rig (measured: −78% gate time vs letting the runner go hunting)
#  - the runner is never told it is being scored or timed
PROMPT="Run the bullshit-detector skill end to end on the transcript at $TRANSCRIPT.
The skill is installed at $SKILL — read its SKILL.md and follow it. The transcript is
already fetched and normalized; do not fetch anything about the source video. Do not
read any directory named examples/ and do not look at any prior report of any content:
work only from the transcript and your own verification searches. Write the finished
report to $REPORT and its run record beside it. Use the skill's scripts from their
installed paths; do not modify any skill file."

MODEL_ARGS=()
[ -n "${EVAL_MODEL:-}" ] && MODEL_ARGS+=(--model "$EVAL_MODEL")
MODEL_ARGS+=(--effort "${EVAL_EFFORT:-xhigh}")

claude -p "$PROMPT" "${MODEL_ARGS[@]}" --permission-mode bypassPermissions

echo
uv run "$(dirname "$0")/score.py" "$CASE_DIR" "$REPORT"
