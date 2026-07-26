#!/usr/bin/env bash
# Deliver dashboard.html + tz-01..tz-15.html to Telegram via your own bot.
#
# Required env:
#   TELEGRAM_BOT_TOKEN  -- token from @BotFather
#   TELEGRAM_CHAT_ID    -- where to send (your own user id, or a chat/channel id)
# Optional env:
#   TELEGRAM_EXPECT_BOT -- bot username to assert before sending, e.g. mycontentbot
#
# Usage: 11-deliver-telegram.sh <output_dir>
set -euo pipefail

OUT="${1:?usage: 11-deliver-telegram.sh <output_dir>}"
: "${TELEGRAM_BOT_TOKEN:?TELEGRAM_BOT_TOKEN env var is required}"
CHAT_ID="${TELEGRAM_CHAT_ID:?TELEGRAM_CHAT_ID env var is required}"

# Identity check: confirm the token belongs to the bot you think it does.
# Set TELEGRAM_EXPECT_BOT to fail fast when the wrong token is exported.
IDENTITY=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('result',{}).get('username',''))")

if [ -z "$IDENTITY" ]; then
  echo "IDENTITY_FAIL: getMe returned no username -- check TELEGRAM_BOT_TOKEN" >&2
  exit 3
fi
if [ -n "${TELEGRAM_EXPECT_BOT:-}" ] && [ "$IDENTITY" != "$TELEGRAM_EXPECT_BOT" ]; then
  echo "IDENTITY_FAIL: expected @$TELEGRAM_EXPECT_BOT, got @$IDENTITY" >&2
  exit 3
fi
echo "[ok] identity: @$IDENTITY"

TG_OUT="$(mktemp -t reel-radar-tg)"
trap 'rm -f "$TG_OUT"' EXIT

send_msg(){
  local TEXT="$1"
  local HTTP
  HTTP=$(curl -sS -o "$TG_OUT" -w "%{http_code}" -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -F "chat_id=${CHAT_ID}" -F "parse_mode=HTML" --form-string "text=${TEXT}")
  if [ "$HTTP" != "200" ]; then
    echo "WARN sendMessage HTTP $HTTP: $(cat "$TG_OUT" 2>/dev/null | head -c 300)" >&2
  fi
}

send_doc(){
  local FILE="$1"
  local CAPTION="$2"
  local HTTP
  HTTP=$(curl -sS -o "$TG_OUT" -w "%{http_code}" -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
    -F "chat_id=${CHAT_ID}" \
    -F "document=@${FILE}" \
    --form-string "caption=${CAPTION}" \
    -F "parse_mode=HTML")
  if [ "$HTTP" != "200" ]; then
    echo "WARN sendDocument $FILE HTTP $HTTP: $(cat "$TG_OUT" 2>/dev/null | head -c 300)" >&2
  fi
}

# Stats from state files
STATS=$(python3 - "$OUT" <<'PYEOF'
import json, sys
from pathlib import Path
o = Path(sys.argv[1])
try:
    top25 = json.loads((o/"state/reels-top25.json").read_text())
    top15 = json.loads((o/"state/reels-top15.json").read_text())
    own = json.loads((o/"state/own-reels.json").read_text())
    following = json.loads((o/"state/following.json").read_text())
    relevant = json.loads((o/"state/reels-relevant.json").read_text())
    total_v = sum(int(r.get("play_count",0)) for r in top25)
    print(f"{len(following)}|{len(relevant)}|{len(top25)}|{len(top15)}|{len(own)}|{total_v}")
except Exception as e:
    print(f"0|0|0|0|0|0")
PYEOF
)
IFS='|' read -r FOLLOW REL TOP25 TOP15 OWN TOTAL_V <<< "$STATS"

WINDOW_TO=$(date "+%Y-%m-%d")
WINDOW_FROM=$(date -v-7d "+%Y-%m-%d" 2>/dev/null || date -d "7 days ago" "+%Y-%m-%d")

# 1. Intro
INTRO="<b>Reel Radar</b> — разведка завершена

Окно: <code>${WINDOW_FROM}</code> → <code>${WINDOW_TO}</code> (7 дней)
Подписок просканировано: <b>${FOLLOW}</b>
Релевантных рилсов: <b>${REL}</b>
Топ-25 для дашборда: <b>${TOP25}</b>
Топ-15 для съёмки: <b>${TOP15}</b>
Референсов из твоего аккаунта за 30 дней: <b>${OWN}</b>
Суммарные просмотры топ-25: <b>${TOTAL_V}</b>

Сейчас придёт дашборд + 15 ТЗ."

send_msg "$INTRO"

# 2. Dashboard
if [ -f "$OUT/dashboard.html" ]; then
  send_doc "$OUT/dashboard.html" "<b>Dashboard</b> — 25 рилсов со статистикой, формулами, темами"
else
  echo "WARN: dashboard.html missing" >&2
fi

# 3. 15 TZ HTMLs
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15; do
  TZ="$OUT/tz-${i}.html"
  if [ -f "$TZ" ]; then
    send_doc "$TZ" "ТЗ ${i}/15"
    sleep 0.4
  fi
done

# 4. Final instructions
FINAL="<b>Готово.</b>

15 ТЗ приоритизированы по релевантности твоего аккаунта (тема + формула + engagement-профиль).

<b>Как применить:</b>
• Открой dashboard.html – выбери 1-3 самых горящих формулы
• Открой tz-01.html (самый релевантный) – записывай по телесуфлёру
• Монтажный timeline передай монтажёру как есть
• В описании поста – код-слово из ТЗ

Следующий прогон: скажи <i>\"разведка рилсов\"</i>."

send_msg "$FINAL"
echo "[ok] delivered to chat_id=${CHAT_ID}"
