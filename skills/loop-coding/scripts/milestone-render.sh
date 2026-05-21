#!/usr/bin/env bash
# Usage: milestone-render.sh <phase-num> [<total>]
# Prints a bar and percentage. phase 0=Init, 1..7 named, total default 7.
set -euo pipefail

PHASE="${1:?phase required}"
TOTAL="${2:-7}"
PHASES=("Research" "Audit" "Plan" "Implement" "Review" "Fix-loop" "Ship")

if (( PHASE < 0 || PHASE > TOTAL )); then
  echo "invalid phase: $PHASE (expected 0..$TOTAL)" >&2
  exit 1
fi

FILLED=""
EMPTY=""
for ((i=1; i<=TOTAL; i++)); do
  if (( i <= PHASE )); then FILLED+="▰"; else EMPTY+="▱"; fi
done

PERCENT=$(( PHASE * 100 / TOTAL ))

if (( PHASE == 0 )); then
  LABEL="Init"
else
  LABEL="${PHASES[$((PHASE-1))]:-Phase $PHASE}"
fi

printf "%s%s %d%% · %s\n" "$FILLED" "$EMPTY" "$PERCENT" "$LABEL"
