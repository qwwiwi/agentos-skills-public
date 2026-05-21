#!/usr/bin/env bash
# Usage: skill-scout.sh "<query>"
# Searches skills.sh catalog. Returns JSON.
# Note: skills.sh search API is placeholder — falls back to curl of main page.
set -euo pipefail

QUERY="${1:?query required}"

# Placeholder: skills.sh search API. If unavailable, return empty result.
# When skills.sh exposes /api/search, replace this block.
CATALOG_URL="${SKILLS_SH_API:-https://skills.sh/api/search}"

RESP=$(curl -fsS --max-time 15 "$CATALOG_URL?q=$(printf '%s' "$QUERY" | jq -sRr @uri)" 2>/dev/null || echo '')

if [[ -z "$RESP" || "$RESP" == *"<!DOCTYPE"* ]]; then
  # API not available — return empty, orchestrator falls back to Sonar
  echo '{"results":[],"note":"skills.sh API unavailable; use Sonar fallback"}'
  exit 0
fi

echo "$RESP"
