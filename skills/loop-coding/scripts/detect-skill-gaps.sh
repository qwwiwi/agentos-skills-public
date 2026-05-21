#!/usr/bin/env bash
# Usage: detect-skill-gaps.sh <run-dir>
# Parses AUDIT.md for "Missing tools" / "Missing-tools" section, prints gaps.
set -euo pipefail

RUN_DIR="${1:?run dir required}"
AUDIT="$RUN_DIR/AUDIT.md"

[[ -f "$AUDIT" ]] || { echo "no AUDIT.md yet"; exit 0; }

awk '
  BEGIN { in_section=0 }
  {
    lower = tolower($0)
    if (lower ~ /^## *missing[- ]tools/) { in_section=1; next }
    if (/^## / && in_section) { in_section=0 }
    if (in_section && /^[-*] /) { sub(/^[-*] /,""); print }
  }
' "$AUDIT"
