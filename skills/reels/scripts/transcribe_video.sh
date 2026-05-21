#!/bin/bash
set -euo pipefail

# Transcribe video/audio file using mlx_whisper (local) or groq (API)
# Usage: transcribe_video.sh /path/to/file.mp4

FILE_PATH="${1:-}"
LANG="${2:-ru}"

if [ -z "$FILE_PATH" ]; then
  echo "Usage: transcribe_video.sh /path/to/file [language]"
  exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
  echo "ERROR: File not found: $FILE_PATH"
  exit 1
fi

MLX_WHISPER="$(command -v mlx_whisper 2>/dev/null || echo "")"

if [ -n "$MLX_WHISPER" ] && [ -x "$MLX_WHISPER" ]; then
  $MLX_WHISPER --language "$LANG" \
    --model mlx-community/whisper-large-v3-turbo \
    --output-dir /tmp \
    --verbose True \
    "$FILE_PATH" 2>&1
else
  echo "ERROR: mlx_whisper not found. Install: pip3 install mlx-whisper"
  exit 1
fi
