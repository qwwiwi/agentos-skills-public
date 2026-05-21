#!/usr/bin/env bash
# Usage: escalate.sh <run-dir>
# Sends REVIEW.md + FIX-LOG.md to prince via Telegram sendDocument.
# Token passed as form field (not URL) to avoid leaks in curl error output / shell history.
set -euo pipefail

RUN_DIR="${1:?run dir required}"
SLUG=$(basename "$RUN_DIR")
TOKEN_FILE="~/.claude/secrets/telegram-bot-token"
CHAT_ID="${PRINCE_CHAT_ID:-<your-telegram-id>}"

[[ -f "$TOKEN_FILE" ]] || { echo "missing telegram token"; exit 1; }
TOKEN=$(cat "$TOKEN_FILE")

CAPTION="loop-coding: итерация 3/3 не сошлась по задаче ${SLUG}. Нужна оценка."

SENT=0
FAILED=0
for FILE in REVIEW.md FIX-LOG.md; do
  [[ -f "$RUN_DIR/$FILE" ]] || continue
  if curl -sS --fail --retry 3 --retry-delay 2 --max-time 30 \
      -X POST "https://api.telegram.org/bot${TOKEN}/sendDocument" \
      -F "chat_id=${CHAT_ID}" \
      -F "document=@${RUN_DIR}/${FILE}" \
      -F "caption=${CAPTION} (${FILE})" >/dev/null; then
    SENT=$((SENT+1))
  else
    echo "send failed for $FILE" >&2
    FAILED=$((FAILED+1))
  fi
done

if (( FAILED > 0 )); then
  echo "escalation partial: $SENT sent, $FAILED failed" >&2
  exit 1
fi

echo "escalated to prince ($CHAT_ID): $SENT files"
