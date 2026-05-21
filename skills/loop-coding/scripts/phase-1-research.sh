#!/usr/bin/env bash
# Usage: phase-1-research.sh <run-dir> <question>
# Preps Phase 1 research. Launches GitHub + skills scouts (scriptable);
# writes a brief for Sonar + code-research subagents (orchestrator spawns them).
set -euo pipefail
RUN_DIR="${1:?run dir required}"
QUESTION="${2:?research question required}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "$QUESTION" > "$RUN_DIR/.research-question"

# GitHub scout (scriptable)
bash "$SCRIPT_DIR/github-search.sh" "$QUESTION" > "$RUN_DIR/research-github.md" 2>"$RUN_DIR/.github-search.err" || true

# Skills scout (scriptable)
bash "$SCRIPT_DIR/skill-scout.sh" "$QUESTION" > "$RUN_DIR/research-skills.md" 2>"$RUN_DIR/.skill-scout.err" || true

# Briefs for subagents the orchestrator must spawn
cat > "$RUN_DIR/.research-brief.md" <<BRIEF
# Research brief (phase 1)

Question: $QUESTION
RUN_DIR: $RUN_DIR

## Scriptable scouts (already run)

- research-github.md
- research-skills.md

## Agents the orchestrator must spawn in parallel

1. Sonar (Perplexity sonar-pro) -> $RUN_DIR/research-sonar.md
   Query: "$QUESTION — best practices, pitfalls, 2026"
2. code-research subagent (Sonnet) -> $RUN_DIR/research-code.md
   Read: your-repos, ~/.claude/ — existing patterns for the task.

When both return: bash scripts/merge-research.sh "$RUN_DIR"
BRIEF

echo "$RUN_DIR/.research-brief.md"
