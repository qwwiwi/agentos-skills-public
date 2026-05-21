#!/usr/bin/env bash
# Usage: merge-plan.sh <run-dir>
# Merges plan-arch.md (Codex) + plan-impl.md (Opus) into PLAN.md.
set -euo pipefail
RUN_DIR="${1:?run dir required}"
ARCH="$RUN_DIR/plan-arch.md"
IMPL="$RUN_DIR/plan-impl.md"
OUT="$RUN_DIR/PLAN.md"
{
  echo "# PLAN (merged)"
  echo ""
  echo "Generated: $(date -u +%FT%TZ)"
  echo ""
  echo "## Architecture (Codex)"
  echo ""
  [[ -f "$ARCH" ]] && cat "$ARCH" || echo "_(missing $ARCH)_"
  echo ""
  echo "## Implementation plan (Opus)"
  echo ""
  [[ -f "$IMPL" ]] && cat "$IMPL" || echo "_(missing $IMPL)_"
} > "$OUT"
echo "merged -> $OUT"
