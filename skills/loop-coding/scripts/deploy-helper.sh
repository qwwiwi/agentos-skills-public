#!/usr/bin/env bash
# Usage: deploy-helper.sh <env> <run-dir>
# env: staging | production
# Wraps the project's scripts/deploy.sh with MANDATORY backup + verification.
#
# Production gate: requires LOOP_CODING_PROD_APPROVED=yes (set by orchestrator
# AFTER prince explicit OK: "да, на prod"). Defense in depth vs SKILL.md policy.
# Staging: autonomous but still backup-gated.
set -euo pipefail

ENV="${1:?env required}"
RUN_DIR="${2:?run dir required}"
DEPLOY_LOG="$RUN_DIR/DEPLOY.md"
HEALTH_URL="${LOOP_CODING_HEALTH_URL:-}"

if [[ "$ENV" != "staging" && "$ENV" != "production" ]]; then
  echo "env must be staging or production" >&2
  exit 1
fi

if [[ "$ENV" == "production" && "${LOOP_CODING_PROD_APPROVED:-}" != "yes" ]]; then
  echo "refusing prod deploy: LOOP_CODING_PROD_APPROVED=yes required (prince explicit OK)" >&2
  exit 3
fi

PROJECT_DEPLOY="scripts/deploy.sh"
if [[ ! -f "$PROJECT_DEPLOY" ]]; then
  echo "no $PROJECT_DEPLOY in project — cannot deploy" | tee -a "$DEPLOY_LOG" >&2
  exit 1
fi

{
  echo "## Deploy: $ENV"
  echo "Timestamp: $(date -u +%FT%TZ)"
  echo "Git HEAD: $(git rev-parse HEAD 2>/dev/null || echo 'n/a')"
  echo ""
} >> "$DEPLOY_LOG"

# Mandatory backup before EVERY deploy (per phase-7-ship.md guardrails)
if ! command -v restic >/dev/null 2>&1; then
  echo "restic not installed — deploy blocked (mandatory backup)" | tee -a "$DEPLOY_LOG" >&2
  exit 4
fi
if [[ -z "${RESTIC_REPOSITORY:-}" ]]; then
  echo "RESTIC_REPOSITORY unset — deploy blocked (mandatory backup)" | tee -a "$DEPLOY_LOG" >&2
  exit 4
fi

echo "Creating restic backup..." | tee -a "$DEPLOY_LOG"
if ! restic backup . --tag "loop-coding-$ENV" 2>&1 | tee -a "$DEPLOY_LOG"; then
  echo "backup FAILED — aborting deploy" | tee -a "$DEPLOY_LOG" >&2
  exit 5
fi

# Run project deploy
echo "Running $PROJECT_DEPLOY $ENV..." | tee -a "$DEPLOY_LOG"
bash "$PROJECT_DEPLOY" "$ENV" 2>&1 | tee -a "$DEPLOY_LOG"
RC=${PIPESTATUS[0]}

if (( RC != 0 )); then
  echo "deploy FAILED with exit $RC" | tee -a "$DEPLOY_LOG" >&2
  exit $RC
fi

# Health check (if configured)
if [[ -n "$HEALTH_URL" ]]; then
  echo "Health-checking $HEALTH_URL..." | tee -a "$DEPLOY_LOG"
  SLEEP=3
  OK=0
  for _ in 1 2 3 4 5; do
    CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$HEALTH_URL" || echo "000")
    echo "  status=$CODE" | tee -a "$DEPLOY_LOG"
    if [[ "$CODE" =~ ^2 ]]; then OK=1; break; fi
    sleep $SLEEP
  done
  if (( OK == 0 )); then
    echo "health check FAILED for $HEALTH_URL — deploy may be broken" | tee -a "$DEPLOY_LOG" >&2
    exit 6
  fi
else
  echo "warning: LOOP_CODING_HEALTH_URL unset — no post-deploy health check" | tee -a "$DEPLOY_LOG" >&2
fi

echo "deploy OK ($ENV)" | tee -a "$DEPLOY_LOG"
