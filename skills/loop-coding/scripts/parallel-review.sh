#!/usr/bin/env bash
# Usage: parallel-review.sh <phase:audit|review> <run-dir>
# Spawns Codex in background and prepares the Opus reviewer brief.
# Orchestrator spawns the Opus subagent via Agent tool (not scriptable).
set -euo pipefail

PHASE="${1:?phase required}"
RUN_DIR="${2:?run dir required}"

if [[ "$PHASE" != "audit" && "$PHASE" != "review" ]]; then
  echo "phase must be audit or review" >&2
  exit 1
fi

# Prepare diff context (review phase only)
if [[ "$PHASE" == "review" ]]; then
  BASE_BRANCH="${LOOP_CODING_BASE:-main}"
  if git rev-parse --verify "$BASE_BRANCH" >/dev/null 2>&1; then
    git diff "$BASE_BRANCH"..HEAD > "$RUN_DIR/.diff-under-review"
    echo "diff prepared: $(wc -l < "$RUN_DIR/.diff-under-review") lines" >&2
  else
    echo "warning: base branch $BASE_BRANCH not found; review will lack diff" >&2
  fi
fi

CODEX_OUT="$RUN_DIR/${PHASE}-codex.md"

# Build Codex prompt
if [[ "$PHASE" == "audit" ]]; then
  CODEX_PROMPT="Audit the codebase at $(pwd) for the loop-coding task in $RUN_DIR. Read RESEARCH.md and PLAN-intent.md if present. Cover ALL of: existing code/patterns to respect, dependency health, security surface, migration risks, test coverage, code quality hotspots, consistency with project patterns, reusable components, suggested boundaries (keep vs rewrite), missing tools where sub-skills/external skills may help. Output AUDIT.md with sections: Existing Code, Risks, Missing Tools, Recommendations, Test Coverage Snapshot. Use severity tags [critical]/[high]/[medium]/[low] on each finding."
else
  CODEX_PROMPT="Review the diff at $RUN_DIR/.diff-under-review plus the full working tree. Check correctness, security, spec adherence vs PLAN.md in $RUN_DIR. Produce markdown with Consensus/Divergent-ready findings, each tagged [critical]/[high]/[medium]/[low] with file:line citations."
fi

# Spawn Codex in background
if command -v codex >/dev/null 2>&1; then
  echo "spawning codex for phase=$PHASE (background)..." >&2
  ( codex exec --skip-git-repo-check "$CODEX_PROMPT" > "$CODEX_OUT" 2>"$RUN_DIR/.codex-${PHASE}.err" ) &
  CODEX_PID=$!
  echo "$CODEX_PID" > "$RUN_DIR/.codex-${PHASE}.pid"
  echo "codex_pid=$CODEX_PID codex_out=$CODEX_OUT" >&2
else
  echo "warning: codex CLI not found; skipping codex reviewer" >&2
  : > "$CODEX_OUT"
fi

# AUDIT phase: Codex-only (Opus removed 2026-04-24, see core/rules.md "Model role split").
# Codex writes AUDIT.md directly. No Opus brief, no merge step.
if [[ "$PHASE" == "audit" ]]; then
  echo "audit phase is Codex-only; orchestrator should wait on PID and rename ${PHASE}-codex.md -> AUDIT.md" >&2
  echo "$CODEX_OUT"
  exit 0
fi

# REVIEW phase: dual-model (Codex + Opus parallel). Write Opus brief for orchestrator.
OPUS_OUT="$RUN_DIR/${PHASE}-opus.md"
OPUS_BRIEF="$RUN_DIR/.opus-brief-${PHASE}.md"

cat > "$OPUS_BRIEF" <<BRIEF
# Opus reviewer brief for phase=$PHASE

RUN_DIR: $RUN_DIR
Expected output: $OPUS_OUT
Codex output (for cross-reference, may still be writing): $CODEX_OUT

## Task

$CODEX_PROMPT

## Instructions to orchestrator

Spawn a code-reviewer subagent (Opus) in parallel with the Codex process (PID at $RUN_DIR/.codex-${PHASE}.pid).
The subagent must write findings to $OPUS_OUT using the same severity tag format [critical]/[high]/[medium]/[low].

When both complete:
  wait \$(cat "$RUN_DIR/.codex-${PHASE}.pid")  # or check file exists
  bash scripts/merge-reviews.sh "$RUN_DIR" "$PHASE"
BRIEF

echo "$OPUS_BRIEF"
