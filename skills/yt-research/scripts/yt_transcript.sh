#!/usr/bin/env bash
# yt-research transcript — TranscriptAPI.com v2 (paid API, 100 free credits on signup).
# Usage: yt_transcript.sh <youtube_url_or_id> [format]   format: text (default) | json
set -euo pipefail

INPUT="${1:?usage: yt_transcript.sh <url|id> [text|json]}"
FMT="${2:-text}"
KEY="${TRANSCRIPT_API_KEY:-$(cat "$HOME/.claude/skills/yt-research/secrets/transcript-api-key" 2>/dev/null || true)}"
[ -n "$KEY" ] || { echo "Set TRANSCRIPT_API_KEY (env) or put the key in ~/.claude/skills/yt-research/secrets/transcript-api-key — get one free at https://transcriptapi.com" >&2; exit 3; }

# Extract the 11-char video id from any YouTube URL form (or accept a bare id).
VID="$(printf '%s' "$INPUT" | python3 -c '
import re, sys
s = sys.stdin.read().strip()
m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", s)
print(m.group(1) if m else (s if re.fullmatch(r"[A-Za-z0-9_-]{11}", s) else ""))
')"
[ -n "$VID" ] || { echo "could not parse a YouTube video id from: $INPUT" >&2; exit 2; }

RESP="$(curl -s --max-time 60 -w $'\n%{http_code}' \
  "https://transcriptapi.com/api/v2/youtube/transcript?video_url=${VID}&format=${FMT}&include_timestamp=false&send_metadata=true" \
  -H "Authorization: Bearer ${KEY}")" || { echo "TranscriptAPI request failed (network)" >&2; exit 1; }
CODE="$(printf '%s' "$RESP" | tail -n1)"
BODY="$(printf '%s' "$RESP" | sed '$d')"

if [ "$CODE" != "200" ]; then
  case "$CODE" in
    401) echo "TranscriptAPI 401 — bad/expired key" >&2 ;;
    402) echo "TranscriptAPI 402 — out of credits, top up at transcriptapi.com/billing" >&2 ;;
    404) echo "TranscriptAPI 404 — this video has no transcript/captions" >&2 ;;
    *)   echo "TranscriptAPI HTTP ${CODE}: $(printf '%s' "$BODY" | head -c 300)" >&2 ;;
  esac
  exit 1
fi

if [ "$FMT" = "json" ]; then
  printf '%s\n' "$BODY"
else
  printf '%s' "$BODY" | python3 -c '
import json, sys
d = json.load(sys.stdin)
m = d.get("metadata", {}) or {}
title, author = m.get("title", ""), m.get("author_name", "")
if title or author:
    print(f"# {title} — {author}\n")
t = d.get("transcript")
print(t if isinstance(t, str) else "\n".join(x.get("text", "") for x in (t or [])))
'
fi
