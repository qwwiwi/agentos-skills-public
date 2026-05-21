#!/usr/bin/env bash
# Usage: github-search.sh "<query>" [<min-stars>] [<limit>]
# Returns JSON array of repos with stars >= min-stars.
# Exit codes: 0 on success (possibly empty []), 2 on auth/CLI error.
set -euo pipefail

QUERY="${1:?query required}"
MIN_STARS="${2:-2000}"
LIMIT="${3:-30}"

if ! command -v gh >/dev/null 2>&1; then
  echo '{"error":"gh CLI not installed"}' >&2
  exit 2
fi

# Check auth up front — separate from "no results"
if ! gh auth status >/dev/null 2>&1; then
  echo '{"error":"gh not authenticated"}' >&2
  exit 2
fi

ERR_FILE=$(mktemp)
trap 'rm -f "$ERR_FILE"' EXIT

if OUT=$(gh search repos "$QUERY stars:>=$MIN_STARS" \
    --sort=stars --order=desc --limit="$LIMIT" \
    --json=fullName,description,stargazersCount,updatedAt,language,licenseInfo,url 2>"$ERR_FILE"); then
  # Success — may still be empty []
  printf '%s\n' "$OUT"
  exit 0
else
  RC=$?
  echo "gh search failed (rc=$RC): $(cat "$ERR_FILE")" >&2
  exit 2
fi
