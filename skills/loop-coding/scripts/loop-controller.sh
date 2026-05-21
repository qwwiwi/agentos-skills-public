#!/usr/bin/env bash
# Usage: loop-controller.sh <run-dir>
# Returns:
#   - "continue" if iteration < 3 AND consensus critical/high remain
#   - "done"     if no consensus critical/high
#   - "escalate" if iteration >= 3 AND consensus critical/high remain
#
# Counts ONLY in the "Consensus" section of REVIEW.md (not Divergent/Raw).
# Increments counter ONLY on continue.
set -euo pipefail

RUN_DIR="${1:?run dir required}"
COUNT_FILE="$RUN_DIR/.iteration-count"
REVIEW="$RUN_DIR/REVIEW.md"

[[ -f "$COUNT_FILE" ]] || echo 0 > "$COUNT_FILE"
COUNT=$(cat "$COUNT_FILE")

REMAINING=0
if [[ -f "$REVIEW" ]]; then
  # Extract only the "## Consensus" block (until next top-level heading)
  CONSENSUS=$(awk '
    /^## Consensus/ { inblock=1; next }
    /^## / && inblock { exit }
    inblock { print }
  ' "$REVIEW")
  # Ignore placeholder template lines
  REMAINING=$(printf '%s\n' "$CONSENSUS" \
    | grep -vE '\[severity\]|\{\{' \
    | grep -cE '\[(critical|high)\]' || true)
fi

if (( REMAINING == 0 )); then
  echo "done"
  exit 0
fi

# Escalate BEFORE doing another iteration if already at the cap
if (( COUNT >= 3 )); then
  echo "escalate"
  exit 0
fi

echo $((COUNT + 1)) > "$COUNT_FILE"
echo "continue"
