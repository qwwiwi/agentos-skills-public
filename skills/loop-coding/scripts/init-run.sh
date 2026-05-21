#!/usr/bin/env bash
# Usage: init-run.sh <task-slug> [<base-dir>]
# Creates a run directory with templates seeded. Prints the RUN_DIR to stdout.
set -euo pipefail

SLUG="${1:?task slug required}"
BASE_DIR="${2:-~/.claude/loop-coding-runs}"
DATE=$(date -u +%Y-%m-%d)
RUN_DIR="$BASE_DIR/${DATE}-${SLUG}"

mkdir -p "$RUN_DIR"/{tests,rented-skills}

# Seed templates from skill's templates/ dir, rendering placeholders
SKILL_DIR="~/.claude/skills/loop-coding"
DATE_UTC="$(date -u +%FT%TZ)"
ITERATION=0
render() {
  local src="$1" dst="$2"
  sed -e "s|{{TASK_SLUG}}|${SLUG}|g" \
      -e "s|{{DATE_UTC}}|${DATE_UTC}|g" \
      -e "s|{{ITERATION}}|${ITERATION}|g" \
      "$src" > "$dst"
}
for f in RESEARCH.md AUDIT.md PLAN.md REVIEW.md FIX-LOG.md DEPLOY.md; do
  if [[ ! -f "$RUN_DIR/$f" ]]; then
    if [[ -f "$SKILL_DIR/templates/$f" ]]; then
      render "$SKILL_DIR/templates/$f" "$RUN_DIR/$f"
    else
      printf "# %s\n\nTask: %s\nStarted: %s\n" "$f" "$SLUG" "$DATE_UTC" > "$RUN_DIR/$f"
    fi
  fi
done

# Ensure persistent sub-skills directory exists
mkdir -p "$SKILL_DIR/sub-skills"

echo 0 > "$RUN_DIR/.iteration-count"
echo "$RUN_DIR"
