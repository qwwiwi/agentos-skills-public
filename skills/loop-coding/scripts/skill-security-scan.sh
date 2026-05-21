#!/usr/bin/env bash
# Usage: skill-security-scan.sh <skill-dir>
# Exit codes: 0 safe, 1 risky, 2 reject
# Output: JSON with verdict + reasons (always valid, uses jq/python for escaping).
set -euo pipefail

SKILL_DIR="${1:?skill directory required}"

emit_json() {
  local verdict="$1"; shift
  local -a reasons=("$@")
  if command -v jq >/dev/null 2>&1; then
    local payload
    payload=$(printf '%s\n' "${reasons[@]:-}" | jq -Rc 'select(length>0)' | jq -s --arg v "$verdict" '{verdict:$v, reasons:.}')
    printf '%s\n' "$payload"
  else
    python3 - "$verdict" "${reasons[@]:-}" <<'PY'
import json, sys
verdict = sys.argv[1]
reasons = [r for r in sys.argv[2:] if r]
print(json.dumps({"verdict": verdict, "reasons": reasons}))
PY
  fi
}

if [[ ! -d "$SKILL_DIR" ]]; then
  emit_json "reject" "directory not found: $SKILL_DIR"
  exit 2
fi

WHITELIST_DOMAINS=(
  'github\.com'
  'raw\.githubusercontent\.com'
  'skills\.sh'
  'pypi\.org'
  'npmjs\.com'
  'registry\.npmjs\.org'
  'anthropic\.com'
  'docs\.anthropic\.com'
)

REJECT_PATTERNS=(
  'curl [^|]*\| *(bash|sh)'
  'wget [^|]*\| *(bash|sh)'
  'rm -rf (/|\$HOME|~)'
  '> */dev/(sda|nvme|disk)'
  'dd if=.* of=/dev/'
  'eval .*\$\{?[A-Za-z_]'
  '~/.secrets'
  '~/.ssh/id_'
  'ssh-keygen -f ~/\.ssh'
  '\.pem([^a-zA-Z]|$)'
  '\.env([^a-zA-Z]|$)'
  '\.key([^a-zA-Z]|$)'
  '/etc/passwd'
  '/etc/shadow'
  'ghp_[A-Za-z0-9]{30,}'
  'sk-[A-Za-z0-9]{30,}'
  'ya29\.[A-Za-z0-9_-]{30,}'
  'chmod 777 (/|~|\$HOME)'
)

RISKY_PATTERNS=(
  'sudo '
  'chmod 777'
  'chown '
  '/etc/'
  'iptables'
  'launchctl '
  'systemctl '
)

VERDICT=safe
REASONS=()

GREP_EXCLUDES=(--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=dist --exclude-dir=build)

scan() {
  local pattern="$1" level="$2"
  if grep -rEq --binary-files=without-match "${GREP_EXCLUDES[@]}" -- "$pattern" "$SKILL_DIR" 2>/dev/null; then
    REASONS+=("${level}: ${pattern}")
    return 0
  fi
  return 1
}

for pattern in "${REJECT_PATTERNS[@]}"; do
  if scan "$pattern" "REJECT"; then
    VERDICT=reject
  fi
done

if [[ "$VERDICT" != "reject" ]]; then
  for pattern in "${RISKY_PATTERNS[@]}"; do
    if scan "$pattern" "RISKY"; then
      VERDICT=risky
    fi
  done
fi

if [[ "$VERDICT" != "reject" ]]; then
  URLS=$(grep -rhoE "${GREP_EXCLUDES[@]}" 'https?://[A-Za-z0-9._-]+' "$SKILL_DIR" 2>/dev/null | sort -u || true)
  while IFS= read -r url; do
    [[ -z "$url" ]] && continue
    host=$(printf '%s' "$url" | sed -E 's#^https?://##' | cut -d/ -f1)
    allowed=0
    for w in "${WHITELIST_DOMAINS[@]}"; do
      if [[ "$host" =~ $w ]]; then allowed=1; break; fi
    done
    if [[ $allowed -eq 0 ]]; then
      REASONS+=("RISKY: non-whitelisted host $host")
      [[ "$VERDICT" == "safe" ]] && VERDICT=risky
    fi
  done <<< "$URLS"
fi

if [[ "$VERDICT" != "reject" ]]; then
  if grep -rEq --binary-files=without-match "${GREP_EXCLUDES[@]}" -- '(>|tee) +/(bin|sbin|usr|etc|var|root)/' "$SKILL_DIR" 2>/dev/null; then
    REASONS+=("RISKY: write to system path")
    [[ "$VERDICT" == "safe" ]] && VERDICT=risky
  fi
fi

emit_json "$VERDICT" "${REASONS[@]:-}"

case "$VERDICT" in
  safe)   exit 0 ;;
  risky)  exit 1 ;;
  reject) exit 2 ;;
esac
