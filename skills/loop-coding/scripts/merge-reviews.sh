#!/usr/bin/env bash
# Usage: merge-reviews.sh <run-dir> <phase:audit|review>
# Merges {phase}-codex.md + {phase}-opus.md into REVIEW.md or AUDIT.md
# with Consensus (both models mention) vs Divergent (one model only) sections.
set -euo pipefail

RUN_DIR="${1:?run dir required}"
PHASE="${2:?phase required}"

CODEX="$RUN_DIR/${PHASE}-codex.md"
OPUS="$RUN_DIR/${PHASE}-opus.md"

case "$PHASE" in
  review) OUT="$RUN_DIR/REVIEW.md" ;;
  audit)  OUT="$RUN_DIR/AUDIT.md" ;;
  *) echo "unsupported phase: $PHASE" >&2; exit 1 ;;
esac

# Wait for codex if still writing (bounded)
CODEX_PID_FILE="$RUN_DIR/.codex-${PHASE}.pid"
if [[ -f "$CODEX_PID_FILE" ]]; then
  pid=$(cat "$CODEX_PID_FILE")
  if kill -0 "$pid" 2>/dev/null; then
    echo "waiting for codex pid=$pid..." >&2
    for _ in $(seq 1 60); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 5
    done
  fi
fi

[[ -f "$CODEX" ]] || { echo "missing $CODEX (codex may have failed)" >&2; : > "$CODEX"; }
[[ -f "$OPUS"  ]] || { echo "missing $OPUS" >&2; exit 1; }

# Extract severity-tagged lines and normalize for comparison
extract_findings() {
  local f="$1"
  # Take lines containing severity tag, normalize whitespace, lowercase
  grep -hE '\[(critical|high|medium|low)\]' "$f" 2>/dev/null \
    | sed -E 's/[[:space:]]+/ /g' \
    | sed -E 's/^[ \t-]+//' \
    | awk 'NF'
}

CODEX_TMP=$(mktemp)
OPUS_TMP=$(mktemp)
trap 'rm -f "$CODEX_TMP" "$OPUS_TMP" "$CODEX_TMP.key" "$OPUS_TMP.key"' EXIT

extract_findings "$CODEX" > "$CODEX_TMP"
extract_findings "$OPUS"  > "$OPUS_TMP"

# Compute a fuzzy key (first 80 chars, lowercase, alphanum only) for each finding
keyify() {
  awk '{
    line=$0
    key=tolower($0)
    gsub(/[^a-z0-9]/, "", key)
    key=substr(key, 1, 80)
    print key "\t" line
  }' "$1"
}

keyify "$CODEX_TMP" > "$CODEX_TMP.key"
keyify "$OPUS_TMP"  > "$OPUS_TMP.key"

# Consensus: keys present in BOTH (present in one = divergent)
CONSENSUS=$(awk -F'\t' 'NR==FNR{a[$1]=$2; next} $1 in a { print "- " a[$1] "\n  (opus) " $2 }' "$CODEX_TMP.key" "$OPUS_TMP.key")
CODEX_ONLY=$(awk -F'\t' 'NR==FNR{a[$1]=1; next} !($1 in a) { print "- " $2 }' "$OPUS_TMP.key" "$CODEX_TMP.key")
OPUS_ONLY=$(awk -F'\t' 'NR==FNR{a[$1]=1; next} !($1 in a) { print "- " $2 }' "$CODEX_TMP.key" "$OPUS_TMP.key")

{
  echo "# ${PHASE^^} (merged)"
  echo ""
  echo "Generated: $(date -u +%FT%TZ)"
  echo ""
  echo "## Consensus (both Codex and Opus agree)"
  echo ""
  echo "${CONSENSUS:-_(none)_}"
  echo ""
  echo "## Divergent — Codex only"
  echo ""
  echo "${CODEX_ONLY:-_(none)_}"
  echo ""
  echo "## Divergent — Opus only"
  echo ""
  echo "${OPUS_ONLY:-_(none)_}"
  echo ""
  echo "## Severity counts (consensus only, used by loop-controller)"
  echo ""
  echo '```'
  printf 'critical: %s\n' "$(printf '%s\n' "$CONSENSUS" | grep -cE '\[critical\]' || true)"
  printf 'high    : %s\n' "$(printf '%s\n' "$CONSENSUS" | grep -cE '\[high\]' || true)"
  printf 'medium  : %s\n' "$(printf '%s\n' "$CONSENSUS" | grep -cE '\[medium\]' || true)"
  printf 'low     : %s\n' "$(printf '%s\n' "$CONSENSUS" | grep -cE '\[low\]' || true)"
  echo '```'
  echo ""
  echo "## Raw inputs"
  echo ""
  echo "### Codex ($CODEX)"
  echo ""
  cat "$CODEX" 2>/dev/null || echo "(empty)"
  echo ""
  echo "### Opus ($OPUS)"
  echo ""
  cat "$OPUS" 2>/dev/null || echo "(empty)"
} > "$OUT"

echo "merged -> $OUT"
