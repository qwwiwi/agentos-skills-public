#!/usr/bin/env bash
# Usage: plan-lint.sh <run-dir>
# Verifies PLAN.md has required sections. Exit 0 pass, 1 fail.
set -euo pipefail
RUN_DIR="${1:?run dir required}"
PLAN="$RUN_DIR/PLAN.md"
[[ -f "$PLAN" ]] || { echo "missing $PLAN" >&2; exit 1; }

REQUIRED=(
  "Goal"
  "Deliverable"
  "Steps"
  "Risks"
  "Tests"
)
MISSING=()
for s in "${REQUIRED[@]}"; do
  grep -qE "^#{1,3} +$s" "$PLAN" || MISSING+=("$s")
done

if (( ${#MISSING[@]} > 0 )); then
  printf 'missing sections: %s\n' "${MISSING[*]}" >&2
  exit 1
fi
echo "plan-lint: OK"
