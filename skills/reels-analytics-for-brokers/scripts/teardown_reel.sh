#!/usr/bin/env bash
# Step 5: tear one reel apart — video, first-3-seconds storyboard, audio,
# transcript, comments.
#
# The first three seconds decide whether a reel travels, so they get sampled
# every half second: six frames is enough to see whether the video opens on a
# text plate, a face, or a cut, and enough to compare openings across dozens of
# reels without watching any of them end to end.
#
# Requires: python3, ffmpeg (https://ffmpeg.org), curl (only for Groq)
# Env:      LOORE_API_KEY (required)  — app.loore.ai → Настройки → API и MCP,
#                                       docs https://docs.loore.ai
#           LOORE_SPEND_AUTHORIZATION_ID (paid calls) — python3 scripts/loore.py approve ...
#           GROQ_API_KEY  (optional)  — https://console.groq.com, enables transcription
#           LOORE_TRANSCRIBE=1 (optional) — transcribe via Loore video-transcribe
#                                       instead (3 credits per reel up to 10 min)
#
# All Loore calls go through scripts/loore_ig.py: the key is read from the
# environment there and never appears in argv or in this script's output.
#
# Usage: ./teardown_reel.sh <REEL_CODE> <OUTPUT_DIR>
#   REEL_CODE is the part after /reel/ in the URL: instagram.com/reel/ABC123/ -> ABC123

set -euo pipefail

CODE="${1:?usage: teardown_reel.sh <REEL_CODE> <OUTPUT_DIR>}"
OUT_ROOT="${2:?usage: teardown_reel.sh <REEL_CODE> <OUTPUT_DIR>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOORE_IG="${HERE}/loore_ig.py"

log() { echo "[teardown ${CODE}] $*" >&2; }

if [ -z "${LOORE_API_KEY:-}" ]; then
  log "LOORE_API_KEY не задан – создайте ключ в https://app.loore.ai → Настройки → API и MCP (документация: https://docs.loore.ai)"
  exit 3
fi

# The code is fed straight into a URL and a directory path, and in the batch
# loop it comes from API data rather than from a human. Anything outside the
# shortcode alphabet is rejected rather than escaped — there is no legitimate
# reel code that needs more than this.
if ! printf '%s' "$CODE" | grep -Eq '^[A-Za-z0-9_-]{1,64}$'; then
  log "invalid reel code (expected [A-Za-z0-9_-], 1-64 chars)"
  exit 2
fi

if [ ! -f "$LOORE_IG" ]; then
  log "missing helper: $LOORE_IG"
  exit 2
fi

DIR="${OUT_ROOT}/${CODE}"
mkdir -p "$DIR/frames"

for binary in python3 ffmpeg; do
  command -v "$binary" >/dev/null 2>&1 || { log "missing dependency: $binary"; exit 2; }
done

# Cached teardowns are free: a published reel never changes, so re-running the
# radar every week should not re-download anything it already has. metadata-only
# teardowns (private or deleted reels, non-video posts) are marked so they are
# not re-fetched.
if [ -s "$DIR/meta.json" ] && { [ -n "$(ls -A "$DIR/frames" 2>/dev/null)" ] || [ -f "$DIR/.no_video" ]; }; then
  log "already torn down, skipping (delete $DIR to force)"
  exit 0
fi

# ig-media: metrics, the whole caption and the numeric media id -> meta.json.
log "fetching media info"
status=0
python3 "$LOORE_IG" media "$CODE" "$DIR/meta.json" || status=$?
if [ "$status" -eq 4 ]; then
  log "no video (private, deleted, or not a video) — stopping after metadata"
  touch "$DIR/.no_video"
  exit 0
elif [ "$status" -ne 0 ]; then
  exit "$status"
fi
MEDIA_PK="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1],encoding="utf-8")).get("pk",""))' "$DIR/meta.json")"

# ig-download (0.5 credits per delivered file). The signed link it returns
# lives about 15 minutes, so loore_ig.py fetches the file at once and never
# writes the link to disk.
log "downloading video"
status=0
python3 "$LOORE_IG" download "$CODE" "$DIR/video.mp4" || status=$?
if [ "$status" -eq 4 ]; then
  log "Loore delivered no file — stopping after metadata"
  touch "$DIR/.no_video"
  exit 0
elif [ "$status" -ne 0 ]; then
  exit "$status"
fi

log "storyboarding first 3 seconds at 0.5s intervals"
ffmpeg -nostdin -loglevel error -y -i "$DIR/video.mp4" -t 3 -vf "fps=2" "$DIR/frames/f_%02d.jpg"

log "extracting audio"
ffmpeg -nostdin -loglevel error -y -i "$DIR/video.mp4" -vn -ac 1 -ar 16000 -c:a libopus -b:a 64k "$DIR/audio.ogg"

if [ -n "${GROQ_API_KEY:-}" ]; then
  command -v curl >/dev/null 2>&1 || { log "missing dependency: curl"; exit 2; }
  # --fail-with-body arrived in curl 7.76; Debian 11 and Ubuntu 20.04 still ship
  # older builds where the unknown flag aborts the script with an opaque error.
  if curl --help all 2>/dev/null | grep -q -- '--fail-with-body'; then
    CURL_FAIL=(--fail-with-body)
  else
    CURL_FAIL=(-f)
  fi
  log "transcribing via Groq Whisper"
  if curl -sS "${CURL_FAIL[@]}" https://api.groq.com/openai/v1/audio/transcriptions \
      -H "Authorization: Bearer ${GROQ_API_KEY}" \
      -F "file=@${DIR}/audio.ogg" \
      -F "model=whisper-large-v3-turbo" \
      -F "response_format=text" \
      -o "$DIR/transcript.txt"; then
    log "transcript: $(wc -c <"$DIR/transcript.txt" | tr -d ' ') bytes"
  else
    log "transcription failed — check GROQ_API_KEY and the response body above"
    rm -f "$DIR/transcript.txt"
  fi
elif [ "${LOORE_TRANSCRIBE:-0}" = "1" ]; then
  log "transcribing via Loore video-transcribe"
  if python3 "$LOORE_IG" transcribe "$CODE" "$DIR/transcript.txt"; then
    log "transcript: $(wc -c <"$DIR/transcript.txt" | tr -d ' ') bytes"
  else
    log "transcription unavailable (no speech, too long, or refused — see above)"
    rm -f "$DIR/transcript.txt"
  fi
else
  log "no transcription: set GROQ_API_KEY (https://console.groq.com) or LOORE_TRANSCRIBE=1"
fi

# The media id comes from parsed JSON; make sure it is a bare number before it
# is passed on.
if printf '%s' "$MEDIA_PK" | grep -Eq '^[0-9]+$'; then
  log "fetching comments"
  python3 "$LOORE_IG" comments "$MEDIA_PK" "$DIR/comments.json" || log "comments unavailable (may be disabled)"
else
  log "no usable media id, skipping comments"
fi

# The video is the bulky part and is only needed to produce frames and audio.
# Keep it only if you plan to watch it: 300 reels is several gigabytes.
if [ "${KEEP_VIDEO:-0}" != "1" ]; then
  rm -f "$DIR/video.mp4"
  log "removed video.mp4 (set KEEP_VIDEO=1 to keep it)"
fi

log "done -> $DIR"
