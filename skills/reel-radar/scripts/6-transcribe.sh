#!/usr/bin/env bash
# Transcribe top-25 videos via Groq Whisper v3-turbo.
# Usage: 6-transcribe.sh <output_dir>
set -euo pipefail

OUT="${1:?usage: 6-transcribe.sh <output_dir>}"
: "${GROQ_KEY:?GROQ_KEY env var is required}"

VIDS="$OUT/videos"
TXT="$OUT/transcripts"
mkdir -p "$TXT"

FFMPEG="$(command -v ffmpeg || echo /opt/homebrew/bin/ffmpeg)"

shopt -s nullglob
for MP4 in "$VIDS"/*.mp4; do
  NAME="$(basename "$MP4" .mp4)"
  IDX="${NAME%%_*}"
  OGG="$TXT/${IDX}.ogg"
  TXT_FILE="$TXT/${IDX}.txt"

  if [ -s "$TXT_FILE" ]; then
    echo "[$IDX] CACHED $TXT_FILE"
    continue
  fi

  "$FFMPEG" -y -i "$MP4" -vn -acodec libopus -b:a 64k "$OGG" >/dev/null 2>&1 || {
    echo "[$IDX] FFMPEG_FAIL"; continue
  }

  RESP=$(curl -s -w $'\n%{http_code}' --max-time 60 \
    "https://api.groq.com/openai/v1/audio/transcriptions" \
    -H "Authorization: Bearer $GROQ_KEY" \
    -F "file=@$OGG" \
    -F "model=whisper-large-v3-turbo" \
    -F "response_format=text")

  HTTP=$(printf '%s\n' "$RESP" | tail -1)
  BODY=$(printf '%s\n' "$RESP" | sed '$d')

  if [ "$HTTP" = "200" ]; then
    printf '%s\n' "$BODY" > "$TXT_FILE"
    LEN=${#BODY}
    echo "[$IDX] OK ${LEN}chars"
  else
    echo "[$IDX] HTTP_$HTTP: $BODY"
  fi
  rm -f "$OGG"
done
