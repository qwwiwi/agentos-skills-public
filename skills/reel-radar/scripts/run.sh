#!/usr/bin/env bash
# Reel Radar orchestrator. Runs 11 steps with state/resume support.
#
# Usage:
#   run.sh                   -- full run, output to /tmp/reel-radar/YYYY-MM-DD
#   run.sh --resume          -- skip completed steps (reads state/progress.json)
#   run.sh --skip-telegram   -- stop before delivery step 11
#   run.sh --out /path       -- custom output directory
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$SKILL_ROOT/scripts"
CONFIG="$SKILL_ROOT/config/defaults.json"

# Parse args
RESUME=0
SKIP_TG=0
CUSTOM_OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --resume) RESUME=1 ;;
    --skip-telegram) SKIP_TG=1 ;;
    --out) CUSTOM_OUT="${2:?--out requires a path}"; shift ;;
    -h|--help) sed -n '3,8p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

DATE=$(date +%Y-%m-%d)

# Tunables live in config/defaults.json; env vars win over the file.
CFG_INTS=$(python3 - "$CONFIG" <<'PYEOF'
import json, sys
DEFAULTS = {"days_subscriptions": 7, "days_own_reels": 30, "top_per_account": 3,
            "top_candidates": 25, "top_final": 15, "parallel_limit": 8,
            "compress_threshold_mb": 50, "cache_ttl_hours": 24}
try:
    cfg = json.load(open(sys.argv[1]))
except Exception:
    cfg = {}
out = []
for key, fallback in DEFAULTS.items():
    try:
        value = int(cfg.get(key, fallback))
    except (TypeError, ValueError):
        value = fallback
    out.append(str(value if value > 0 else fallback))
print(" ".join(out))
PYEOF
)
read -r DAYS_SUBS DAYS_OWN TOP_PER TOP_CAND CFG_TOP_FINAL PARALLEL COMPRESS_MB CACHE_TTL_H <<< "$CFG_INTS"

OUT_TMPL=$(python3 - "$CONFIG" <<'PYEOF'
import json, sys
try:
    print(json.load(open(sys.argv[1])).get("output_dir") or "/tmp/reel-radar/{date}")
except Exception:
    print("/tmp/reel-radar/{date}")
PYEOF
)
OUT="${CUSTOM_OUT:-${OUT_TMPL//\{date\}/$DATE}}"

# Consumed by 5-download-videos.sh and 1-fetch-following.py respectively.
export COMPRESS_THRESHOLD_MB="${COMPRESS_THRESHOLD_MB:-$COMPRESS_MB}"
export CACHE_TTL_HOURS="${CACHE_TTL_HOURS:-$CACHE_TTL_H}"

mkdir -p "$OUT"/{state,videos,transcripts}
PROGRESS="$OUT/state/progress.json"

log(){ printf '\n\033[1;33m[run] %s\033[0m\n' "$*"; }

# Keys come from the environment only -- never from a file inside the skill.
# Optionally keep them in a local, git-ignored env file next to the skill:
#   HIKER_KEY=...  GROQ_KEY=...  TELEGRAM_BOT_TOKEN=...  TELEGRAM_CHAT_ID=...
ENV_FILE="${REEL_RADAR_ENV:-$SKILL_ROOT/.env}"
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

# Accept either naming convention for the data-provider key.
HIKER_KEY="${HIKER_KEY:-${HIKER_API_KEY:-}}"; export HIKER_KEY
GROQ_KEY="${GROQ_KEY:-${GROQ_API_KEY:-}}"; export GROQ_KEY

[ -n "${HIKER_KEY:-}" ] || { echo "ERR: HIKER_KEY is empty (get a key at https://hikerapi.com)" >&2; exit 3; }
[ -n "${GROQ_KEY:-}" ] || { echo "ERR: GROQ_KEY is empty (get a key at https://console.groq.com)" >&2; exit 3; }

# Reference account: env wins, otherwise config/defaults.json must be filled.
TARGET_USER="${TARGET_USER:-$(python3 -c "
import json,sys
try: print(json.load(open('$CONFIG')).get('target_user','') or '')
except Exception: print('')
")}"
export TARGET_USER
[ -n "$TARGET_USER" ] || { echo "ERR: target account not set. export TARGET_USER=<instagram_login> or fill \"target_user\" in $CONFIG" >&2; exit 3; }

is_done(){
  [ "$RESUME" = "1" ] || return 1
  [ -f "$PROGRESS" ] || return 1
  python3 -c "
import json, sys
try:
    p = json.load(open('$PROGRESS'))
    sys.exit(0 if p.get('$1') == 'done' else 1)
except Exception:
    sys.exit(1)
"
}

mark_done(){
  python3 -c "
import json, os, datetime
p = '$PROGRESS'
d = {}
if os.path.exists(p):
    try: d = json.load(open(p))
    except Exception: d = {}
d['$1'] = 'done'
d['timestamp'] = datetime.datetime.now().isoformat(timespec='seconds')
json.dump(d, open(p,'w'), indent=2)
"
}

# --- STEP 1: following ---
if ! is_done step_1_following; then
  log "1/11  fetching @$TARGET_USER following"
  python3 "$SCRIPTS/1-fetch-following.py" "$OUT"
  mark_done step_1_following
else log "1/11  skip (resume)"; fi

# --- STEP 2: reels ---
if ! is_done step_2_reels; then
  log "2/11  fetching reels for each followed account (${DAYS_SUBS}d window, top ${TOP_PER}/account)"
  python3 "$SCRIPTS/2-fetch-reels.py" "$OUT" --days "$DAYS_SUBS" --top "$TOP_PER" --parallel "$PARALLEL"
  mark_done step_2_reels
else log "2/11  skip (resume)"; fi

# --- STEP 3: filter ---
if ! is_done step_3_filter; then
  log "3/11  filtering by keywords"
  python3 "$SCRIPTS/3-filter-relevant.py" "$OUT"
  mark_done step_3_filter
else log "3/11  skip (resume)"; fi

# --- STEP 4: rank ---
if ! is_done step_4_rank; then
  log "4/11  composite ranking → top $TOP_CAND"
  python3 "$SCRIPTS/4-rank-composite.py" "$OUT" --top "$TOP_CAND"
  mark_done step_4_rank
else log "4/11  skip (resume)"; fi

# --- STEP 5: download ---
if ! is_done step_5_download; then
  log "5/11  downloading 25 videos via HikerAPI"
  bash "$SCRIPTS/5-download-videos.sh" "$OUT"
  mark_done step_5_download
else log "5/11  skip (resume)"; fi

# --- STEP 6: transcribe ---
if ! is_done step_6_transcribe; then
  log "6/11  transcribing via Groq Whisper v3-turbo"
  bash "$SCRIPTS/6-transcribe.sh" "$OUT"
  mark_done step_6_transcribe
else log "6/11  skip (resume)"; fi

# --- STEP 7: own reels ---
if ! is_done step_7_own; then
  log "7/11  fetching the reference account's own top reels (30d)"
  python3 "$SCRIPTS/7-fetch-own-reels.py" "$OUT" --days "$DAYS_OWN" --top 10
  mark_done step_7_own
else log "7/11  skip (resume)"; fi

# --- STEP 8: relevance match ---
if ! is_done step_8_relevance; then
  TOP_N="${TOP_FINAL:-$CFG_TOP_FINAL}"
  log "8/11  relevance matching → top $TOP_N"
  python3 "$SCRIPTS/8-relevance-match.py" "$OUT" --top "$TOP_N"
  mark_done step_8_relevance
else log "8/11  skip (resume)"; fi

# --- STEP 9: dashboard ---
if ! is_done step_9_dashboard; then
  log "9/11  generating dashboard.html"
  python3 "$SCRIPTS/9-gen-dashboard.py" "$OUT"
  mark_done step_9_dashboard
else log "9/11  skip (resume)"; fi

# --- STEP 10: TZ ---
if ! is_done step_10_tz; then
  log "10/11  generating 15 ТЗ HTML"
  python3 "$SCRIPTS/10-gen-tz.py" "$OUT"
  mark_done step_10_tz
else log "10/11  skip (resume)"; fi

# --- STEP 11: deliver ---
if [ "$SKIP_TG" = "1" ]; then
  log "11/11  skip (--skip-telegram)"
  log "done. artifacts in $OUT"
  exit 0
fi

if ! is_done step_11_deliver; then
  log "11/11  delivering to Telegram"
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] || { echo "ERR: TELEGRAM_BOT_TOKEN missing (use --skip-telegram to write files only)" >&2; exit 3; }
  [ -n "${TELEGRAM_CHAT_ID:-}" ] || { echo "ERR: TELEGRAM_CHAT_ID missing (use --skip-telegram to write files only)" >&2; exit 3; }
  bash "$SCRIPTS/11-deliver-telegram.sh" "$OUT"
  mark_done step_11_deliver
else log "11/11  skip (resume)"; fi

# Cleanup videos (transcripts retained)
log "cleanup: removing raw videos (transcripts kept)"
rm -rf "$OUT/videos"

log "done. artifacts in $OUT"
