#!/usr/bin/env bash
# Usage: pre-ship.sh <run-dir>
# Verifies all pre-flight checks before Phase 7.
set -euo pipefail

RUN_DIR="${1:?run dir required}"
BASE_BRANCH="${LOOP_CODING_BASE:-main}"
FAIL=0

check() {
  local name="$1"; shift
  if "$@"; then
    echo "  PASS: $name"
  else
    echo "  FAIL: $name" >&2
    FAIL=1
  fi
}

echo "Pre-ship checks for $RUN_DIR:"

# Tests green
check "tests green" bash "$(dirname "${BASH_SOURCE[0]}")/test-runner.sh" auto

# Review clean (no critical/high)
if [[ -f "$RUN_DIR/REVIEW.md" ]]; then
  check "no critical/high in REVIEW.md" \
    bash -c "! grep -qE '\[(critical|high)\]' '$RUN_DIR/REVIEW.md'"
fi

# Branch clean: no uncommitted, staged, or untracked working-tree changes
check "no uncommitted changes" git diff --quiet
check "no staged changes" git diff --cached --quiet
check "no untracked files" bash -c "[[ -z \"\$(git ls-files --others --exclude-standard)\" ]]"

# Not on main/master/production/release
BRANCH=$(git rev-parse --abbrev-ref HEAD)
check "not on protected branch" bash -c "[[ '$BRANCH' != 'main' && '$BRANCH' != 'master' && '$BRANCH' != 'production' && '$BRANCH' != release/* ]]"

# Branch is rebased onto base (no commits in base that are not in HEAD)
if git rev-parse --verify "$BASE_BRANCH" >/dev/null 2>&1; then
  BEHIND=$(git rev-list --count "HEAD..$BASE_BRANCH" 2>/dev/null || echo 1)
  check "branch rebased onto $BASE_BRANCH (0 commits behind)" bash -c "[[ '$BEHIND' == '0' ]]"
else
  echo "  SKIP: base branch $BASE_BRANCH not found locally"
fi

# Secrets not staged
check "no .env / secrets staged" bash -c "! git diff --cached --name-only | grep -qE '(^|/)(\.env|secrets/|.*\.pem|.*\.key|id_rsa|id_ed25519|credentials\.json)$'"

exit $FAIL
