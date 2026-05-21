#!/bin/bash
set -euo pipefail

# Groq Whisper API voice transcription
# Usage: transcribe.sh /path/to/file.ogg

FILE_PATH="${1:-}"

if [ -z "$FILE_PATH" ]; then
  echo "ERROR: No file path provided"
  echo "Usage: transcribe.sh /path/to/file.ogg"
  exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
  echo "ERROR: File not found: $FILE_PATH"
  exit 1
fi

GROQ_KEY="${GROQ_API_KEY:-<YOUR_API_KEY>}"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  --max-time 30 \
  "https://api.groq.com/openai/v1/audio/transcriptions" \
  -H "Authorization: Bearer $GROQ_KEY" \
  -F "file=@$FILE_PATH" \
  -F "model=whisper-large-v3-turbo" \
  -F "response_format=text")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
  echo "Transcript: $BODY"
else
  echo "ERROR: Groq API returned HTTP $HTTP_CODE"
  echo "$BODY"
  exit 1
fi
