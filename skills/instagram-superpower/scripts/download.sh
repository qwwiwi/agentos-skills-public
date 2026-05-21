#!/bin/bash
set -euo pipefail

# download.sh — download media via Cobalt API (self-hosted)
# Usage: download.sh <URL> [audio|video|auto|transcribe]

URL="${1:?Usage: download.sh <URL> [audio|video|auto|transcribe]}"
MODE="${2:-auto}"

COBALT_SERVER="root@<your-server-ip>"
SECRETS_DIR="$HOME/.secrets/cobalt"
API_KEY=$(cat "$SECRETS_DIR/api-key" 2>/dev/null || echo "")

if [ -z "$API_KEY" ]; then
  echo "ERROR: API key not found at $SECRETS_DIR/api-key" >&2
  exit 1
fi

# Determine downloadMode for Cobalt
case "$MODE" in
  audio|transcribe) DL_MODE="audio" ;;
  video) DL_MODE="auto" ;;
  *) DL_MODE="auto" ;;
esac

# Call Cobalt API via SSH (API listens only on localhost)
echo "Requesting Cobalt API..." >&2
RESPONSE=$(ssh "$COBALT_SERVER" "curl -s -X POST 'http://127.0.0.1:9000/' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Api-Key $API_KEY' \
  -d '{\"url\":\"$URL\",\"downloadMode\":\"$DL_MODE\"}'")

STATUS=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','error'))" 2>/dev/null || echo "error")

if [ "$STATUS" = "error" ]; then
  ERROR=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('error',{}).get('code','unknown'))" 2>/dev/null || echo "unknown")
  echo "ERROR: Cobalt returned $ERROR" >&2
  echo "$RESPONSE" >&2
  exit 1
fi

# Get URL and filename
DL_URL=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('url',''))" 2>/dev/null)
FILENAME=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('filename','media.mp4'))" 2>/dev/null)

if [ -z "$DL_URL" ]; then
  echo "ERROR: No download URL in response" >&2
  exit 1
fi

# Download file on the Cobalt server
echo "Downloading $FILENAME..." >&2
ssh "$COBALT_SERVER" "curl -sL -o '/tmp/$FILENAME' '$DL_URL'"

# Copy to local machine
mkdir -p /tmp/downloads
scp "$COBALT_SERVER:/tmp/$FILENAME" "/tmp/downloads/$FILENAME" 2>/dev/null
ssh "$COBALT_SERVER" "rm -f '/tmp/$FILENAME'" 2>/dev/null

LOCAL_PATH="/tmp/downloads/$FILENAME"
echo "Saved: $LOCAL_PATH" >&2

# If transcribe mode — run Groq Whisper or local mlx_whisper
if [ "$MODE" = "transcribe" ]; then
  echo "Transcribing..." >&2

  # Convert to ogg if needed
  AUDIO_PATH="$LOCAL_PATH"
  if [[ "$FILENAME" != *.ogg ]]; then
    AUDIO_PATH="/tmp/downloads/${FILENAME%.*}.ogg"
    ffmpeg -i "$LOCAL_PATH" -vn -acodec libopus "$AUDIO_PATH" -y 2>/dev/null
  fi

  # Check size — Groq limit 25MB
  FILE_SIZE=$(stat -f%z "$AUDIO_PATH" 2>/dev/null || stat --printf="%s" "$AUDIO_PATH" 2>/dev/null)
  if [ "$FILE_SIZE" -gt 25000000 ]; then
    echo "File >25MB, splitting..." >&2
    DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUDIO_PATH" 2>/dev/null | cut -d. -f1)
    CHUNK_DURATION=600  # 10 minutes
    CHUNKS=0
    TRANSCRIPT=""
    for START in $(seq 0 $CHUNK_DURATION $DURATION); do
      CHUNK_PATH="/tmp/downloads/chunk_${CHUNKS}.ogg"
      ffmpeg -i "$AUDIO_PATH" -ss "$START" -t "$CHUNK_DURATION" -c copy "$CHUNK_PATH" -y 2>/dev/null
      CHUNK_TEXT=$(bash ~/.claude/skills/groq-voice/transcribe.sh "$CHUNK_PATH" 2>/dev/null)
      TRANSCRIPT="$TRANSCRIPT$CHUNK_TEXT\n"
      rm -f "$CHUNK_PATH"
      CHUNKS=$((CHUNKS + 1))
    done
    echo -e "$TRANSCRIPT"
  else
    bash ~/.claude/skills/groq-voice/transcribe.sh "$AUDIO_PATH"
  fi
else
  echo "$LOCAL_PATH"
fi
