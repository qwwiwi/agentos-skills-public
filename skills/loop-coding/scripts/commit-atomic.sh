#!/usr/bin/env bash
# Usage: commit-atomic.sh [--push] [--paths "a b c"] "<message>"
# Stages ONLY explicit paths (or already-staged changes), commits atomically.
# NEVER uses `git add -A` (violates global rule; risk of staging secrets).
set -euo pipefail

PUSH=0
PATHS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) PUSH=1; shift ;;
    --paths) PATHS="${2:?paths required}"; shift 2 ;;
    --) shift; break ;;
    -*) echo "unknown flag: $1" >&2; exit 1 ;;
    *) break ;;
  esac
done
MSG="${1:?commit message required}"

# Secret-leak guard BEFORE staging
SECRETS_HIT=""
if [[ -n "$PATHS" ]]; then
  for f in $PATHS; do
    case "$(basename "$f")" in
      .env|.env.*|*.pem|*.key|id_rsa|id_ed25519|credentials.json)
        SECRETS_HIT="$SECRETS_HIT $f" ;;
    esac
  done
fi
if [[ -n "$SECRETS_HIT" ]]; then
  echo "refusing to commit potential secrets:$SECRETS_HIT" >&2
  exit 2
fi

if [[ -n "$PATHS" ]]; then
  # shellcheck disable=SC2086
  git add -- $PATHS
fi

# If nothing staged and nothing changed, skip
if git diff --cached --quiet; then
  if git diff --quiet; then
    echo "no changes to commit"
    exit 0
  fi
  echo "refusing to stage with git add -A; pass --paths \"...\" or stage explicitly" >&2
  exit 1
fi

# Second-level guard: scan staged diff for secret-looking strings
STAGED_SECRETS=$(git diff --cached --unified=0 | grep -E '^\+[^+]' | grep -iE '(ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{30,}|ya29\.[A-Za-z0-9_-]{30,}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|AWS_SECRET_ACCESS_KEY *=|PASSWORD *= *["'"'"']?[A-Za-z0-9])' || true)
if [[ -n "$STAGED_SECRETS" ]]; then
  echo "refusing to commit: possible secret in staged diff:" >&2
  printf '%s\n' "$STAGED_SECRETS" | head -5 >&2
  exit 2
fi

git commit -m "$MSG"

if (( PUSH == 1 )); then
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  if [[ "$BRANCH" == "main" || "$BRANCH" == "master" || "$BRANCH" == production || "$BRANCH" == release/* ]]; then
    echo "refusing to push directly to $BRANCH" >&2
    exit 1
  fi
  git push -u origin "$BRANCH"
fi
