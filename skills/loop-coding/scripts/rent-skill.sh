#!/usr/bin/env bash
# Usage: rent-skill.sh <source-url-or-git> <run-dir> [<name>]
# Downloads, scans (strict), and registers a skill for temporary use.
# Env:
#   LOOP_CODING_ALLOW_RISKY=1  -- orchestrator opt-in to accept risky rentals
set -euo pipefail

SRC="${1:?source required}"
RUN_DIR="${2:?run dir required}"
RAW_NAME="${3:-$(basename "$SRC" .git)}"

# Sanitize NAME: allow [A-Za-z0-9._-] only, strip any path traversal
NAME=$(printf '%s' "$RAW_NAME" | tr -cd 'A-Za-z0-9._-')
if [[ -z "$NAME" || "$NAME" == "." || "$NAME" == ".." ]]; then
  echo "invalid skill name after sanitize: [$RAW_NAME] -> [$NAME]" >&2
  exit 1
fi

RENTED_ROOT="$RUN_DIR/rented-skills"
DEST="$RENTED_ROOT/$NAME"
mkdir -p "$RENTED_ROOT"

# Verify DEST stays inside RENTED_ROOT (defense in depth)
RENTED_ABS=$(cd "$RENTED_ROOT" && pwd -P)
case "$(cd "$(dirname "$DEST")" && pwd -P)/$NAME" in
  "$RENTED_ABS"/*) : ;;
  *) echo "refusing path outside rented-skills: $DEST" >&2; exit 1 ;;
esac

# Download
if [[ "$SRC" == *.git || "$SRC" == git@* ]]; then
  git clone --depth 1 "$SRC" "$DEST"
elif [[ "$SRC" == http*://*.zip || "$SRC" == http*://*.tar.gz ]]; then
  TMP=$(mktemp -d)
  curl -fsSL "$SRC" -o "$TMP/pkg"
  mkdir -p "$DEST"
  tar -xf "$TMP/pkg" -C "$DEST" --strip-components=1 2>/dev/null || unzip -q "$TMP/pkg" -d "$DEST"
  rm -rf "$TMP"
else
  echo "unsupported source: $SRC" >&2
  exit 1
fi

# Security scan (strict: check exit code first, JSON second; never treat unknown as safe)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set +e
VERDICT_JSON=$("$SCRIPT_DIR/skill-security-scan.sh" "$DEST")
SCAN_RC=$?
set -e

VERDICT="unknown"
if command -v jq >/dev/null 2>&1; then
  VERDICT=$(printf '%s' "$VERDICT_JSON" | jq -r '.verdict // "unknown"' 2>/dev/null || echo "unknown")
fi

# Authoritative: exit code 0=safe, 1=risky, 2=reject. Fall back to JSON if rc doesn't match.
case "$SCAN_RC" in
  0) VERDICT="safe" ;;
  1) VERDICT="risky" ;;
  2) VERDICT="reject" ;;
  *) # unknown rc -> treat as reject (fail closed)
     VERDICT="reject" ;;
esac

if [[ "$VERDICT" == "reject" ]]; then
  rm -rf "$DEST"
  echo "rejected: $VERDICT_JSON" >&2
  exit 2
fi

if [[ "$VERDICT" == "risky" ]]; then
  if [[ "${LOOP_CODING_ALLOW_RISKY:-0}" != "1" ]]; then
    rm -rf "$DEST"
    echo "risky rental blocked (set LOOP_CODING_ALLOW_RISKY=1 after orchestrator go/no-go): $VERDICT_JSON" >&2
    exit 3
  fi
  echo "risky rental accepted by orchestrator: $VERDICT_JSON" >&2
fi

# Append to manifest
MANIFEST="$RENTED_ROOT/.rental-manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
  echo '{"rentals":[]}' > "$MANIFEST"
fi

SHA=$(find "$DEST" -type f -exec shasum -a 256 {} + 2>/dev/null | sort | shasum -a 256 | awk '{print $1}')
ENTRY=$(jq -n --arg n "$NAME" --arg s "$SRC" --arg v "$VERDICT" --arg h "$SHA" --arg t "$(date -u +%FT%TZ)" \
  '{name:$n, source:$s, security_verdict:$v, sha256:$h, downloaded_at:$t, used_phases:[]}')
jq ".rentals += [$ENTRY]" "$MANIFEST" > "$MANIFEST.tmp" && mv "$MANIFEST.tmp" "$MANIFEST"

echo "$DEST"
