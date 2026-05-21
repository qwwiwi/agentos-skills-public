#!/usr/bin/env bash
set -euo pipefail

# send-thread-draft.sh — send Threads draft to user for approval
# (banner + 7 posts in pre-blocks for one-click copy) via Telegram bot.
#
# Usage:
#   ./send-thread-draft.sh --posts /tmp/thread-posts.txt --banner /tmp/banner.png --slug cognee-vs-obsidian
#   ./send-thread-draft.sh --posts /tmp/thread-posts.txt --slug mcp-memory  (no banner)
#
# Format /tmp/thread-posts.txt: posts separated by a line containing only "---"

POSTS_FILE=""
BANNER_FILE=""
SLUG="thread"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --posts)  POSTS_FILE="$2"; shift 2 ;;
    --banner) BANNER_FILE="$2"; shift 2 ;;
    --slug)   SLUG="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --posts <file> [--banner <png>] [--slug <slug>]"
      echo "Posts file: separate posts with line containing only ---"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$POSTS_FILE" || ! -f "$POSTS_FILE" ]]; then
  echo "Error: --posts file required and must exist" >&2
  exit 1
fi

# Bot token — set via environment variable or key file
if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
elif [[ -f "$HOME/.secrets/telegram-bot-token" ]]; then
  BOT_TOKEN=$(cat "$HOME/.secrets/telegram-bot-token")
else
  echo "Error: bot token not found. Set TELEGRAM_BOT_TOKEN or create ~/.secrets/telegram-bot-token" >&2
  exit 1
fi

# Target chat ID — set via env or default
CHAT_ID="${TELEGRAM_CHAT_ID:-<your-telegram-id>}"

mapfile -t POSTS < <(awk 'BEGIN{RS="\n---\n"} {print; print "<<<SEP>>>"}' "$POSTS_FILE" | sed 's/<<<SEP>>>/\x1c/g' | tr '\x1c' '\n' | grep -v '^$' || true)
COUNT=${#POSTS[@]}

if [[ $COUNT -lt 5 || $COUNT -gt 8 ]]; then
  echo "Warning: $COUNT posts found, expected 5-8. Proceeding anyway." >&2
fi

if [[ -n "$BANNER_FILE" && -f "$BANNER_FILE" ]]; then
  echo "→ Sending banner..."
  curl -sS -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendPhoto" \
    -F "chat_id=${CHAT_ID}" \
    -F "photo=@${BANNER_FILE}" \
    -F "caption=Banner for thread <b>${SLUG}</b> (first post)" \
    -F "parse_mode=HTML" >/dev/null
fi

HTML="<b>Threads thread: ${SLUG}</b>%0A%0A"
HTML+="Ready for approval. Each post in its own block — copy with one tap.%0A%0A"

i=1
TOTAL=$COUNT
for POST in "${POSTS[@]}"; do
  ESCAPED=$(echo "$POST" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
  HTML+="<pre>${i}/${TOTAL}%0A%0A${ESCAPED}</pre>%0A%0A"
  i=$((i+1))
done

HTML+="Say the word — publish to Threads."

echo "→ Sending draft..."
curl -sS -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "parse_mode=HTML" \
  -d "disable_web_page_preview=true" \
  --data-urlencode "text=${HTML}" >/dev/null

echo "Done. Thread draft sent ($COUNT posts, slug=$SLUG)"
echo "  Awaiting user approval before posting to Threads."
