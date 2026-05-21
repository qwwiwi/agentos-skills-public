#!/usr/bin/env bash
# Usage: merge-research.sh <run-dir>
# Merges research outputs from 4 subagents into RESEARCH.md.
set -euo pipefail
RUN_DIR="${1:?run dir required}"
OUT="$RUN_DIR/RESEARCH.md"
{
  echo "# RESEARCH (merged)"
  echo ""
  echo "Generated: $(date -u +%FT%TZ)"
  echo ""
  for section in sonar code github skills; do
    f="$RUN_DIR/research-${section}.md"
    echo "## ${section^^}"
    echo ""
    if [[ -f "$f" ]]; then
      cat "$f"
    else
      echo "_(no $section output)_"
    fi
    echo ""
  done
} > "$OUT"
echo "merged -> $OUT"
