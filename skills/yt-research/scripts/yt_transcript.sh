#!/usr/bin/env bash
# yt-research transcript – Loore yt_transcript (public captions, 2 credits per transcript).
# Usage: yt_transcript.sh <youtube_url_or_id> [format]   format: text (default) | json
# Needs LOORE_API_KEY (https://app.loore.ai → Настройки → API и MCP); paid calls also take
# LOORE_SPEND_AUTHORIZATION_ID (see scripts/_loore.py approve).
set -euo pipefail

INPUT="${1:?usage: yt_transcript.sh <url|id> [text|json]}"
FMT="${2:-text}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$FMT" in
  text) exec python3 "$DIR/yt_transcript.py" "$INPUT" ;;
  json) exec python3 "$DIR/yt_transcript.py" "$INPUT" --json ;;
  *) echo "format must be text or json, got: $FMT" >&2; exit 2 ;;
esac
