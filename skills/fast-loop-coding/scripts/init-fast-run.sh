#!/usr/bin/env bash
# init-fast-run.sh — minimal run dir for fast-loop-coding.
# Usage: init-fast-run.sh <slug>
# Prints absolute path to created run-dir.
set -euo pipefail

SLUG="${1:?slug required (e.g. add-posttool-failure-hook)}"
DATE="$(date +%Y-%m-%d)"
BASE="~/.claude/loop-coding-runs"
RUN_DIR="$BASE/${DATE}-fast-${SLUG}"

mkdir -p "$RUN_DIR"

# Skeleton: PLAN.md only (review goes inline, no separate REVIEW.md required).
cat > "$RUN_DIR/PLAN.md" <<EOF
# ${SLUG} — fast-loop

Goal: <one sentence>
Files: <list, absolute paths>
Est LOC: <number>
Tests: <how — file + cases>
Rollback: <command or revert hash>

## Steps
1. 
2. 
3. 

## Risks
- <risk> -> <mitigation>

## Review verdict
(filled after Phase 3)

## Ship
(filled after Phase 4: commits, push, handoff entry)
EOF

echo "$RUN_DIR"
