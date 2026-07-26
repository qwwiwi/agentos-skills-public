#!/usr/bin/env bash
# Step 5: tear one reel apart — video, first-3-seconds storyboard, audio,
# transcript, comments.
#
# The first three seconds decide whether a reel travels, so they get sampled
# every half second: six frames is enough to see whether the video opens on a
# text plate, a face, or a cut, and enough to compare openings across dozens of
# reels without watching any of them end to end.
#
# Requires: curl, python3, ffmpeg (https://ffmpeg.org)
# Env:      HIKER_API_KEY (required)  — https://hikerapi.com
#           GROQ_API_KEY  (optional)  — https://console.groq.com, enables transcription
#
# Usage: ./teardown_reel.sh <REEL_CODE> <OUTPUT_DIR>
#   REEL_CODE is the part after /reel/ in the URL: instagram.com/reel/ABC123/ -> ABC123

set -euo pipefail

CODE="${1:?usage: teardown_reel.sh <REEL_CODE> <OUTPUT_DIR>}"
OUT_ROOT="${2:?usage: teardown_reel.sh <REEL_CODE> <OUTPUT_DIR>}"
BASE_URL="${HIKER_BASE_URL:-https://api.instagrapi.com}"
: "${HIKER_API_KEY:?HIKER_API_KEY is not set — get a key at https://hikerapi.com}"

log() { echo "[teardown ${CODE}] $*" >&2; }

# The code is fed straight into a URL and a directory path, and in the batch
# loop it comes from API data rather than from a human. Anything outside the
# shortcode alphabet is rejected rather than escaped — there is no legitimate
# reel code that needs more than this.
if ! printf '%s' "$CODE" | grep -Eq '^[A-Za-z0-9_-]{1,64}$'; then
  log "invalid reel code (expected [A-Za-z0-9_-], 1-64 chars)"
  exit 2
fi

DIR="${OUT_ROOT}/${CODE}"
mkdir -p "$DIR/frames"

for binary in curl python3 ffmpeg; do
  command -v "$binary" >/dev/null 2>&1 || { log "missing dependency: $binary"; exit 2; }
done

# --fail-with-body arrived in curl 7.76; Debian 11 and Ubuntu 20.04 still ship
# older builds where the unknown flag aborts the script with an opaque error.
if curl --help all 2>/dev/null | grep -q -- '--fail-with-body'; then
  CURL_FAIL=(--fail-with-body)
else
  CURL_FAIL=(-f)
fi

# The signed URL must not outlive the download, even if the script dies between
# writing and deleting it.
cleanup() { rm -f "$DIR/.video_url"; }
trap cleanup EXIT

# Cached teardowns are free: a published reel never changes, so re-running the
# radar every week should not re-download anything it already has. metadata-only
# teardowns (private or deleted reels) are marked so they are not re-fetched.
if [ -s "$DIR/meta.json" ] && { [ -n "$(ls -A "$DIR/frames" 2>/dev/null)" ] || [ -f "$DIR/.no_video" ]; }; then
  log "already torn down, skipping (delete $DIR to force)"
  exit 0
fi

log "fetching media info"
curl -sS "${CURL_FAIL[@]}" "${BASE_URL}/v2/media/info/by/code?code=${CODE}" \
  -H "accept: application/json" -H "x-access-key: ${HIKER_API_KEY}" -o "$DIR/media.json"

# Response shapes differ between endpoint versions, so hunt for the fields
# instead of assuming one layout. Paths go in as argv, never spliced into the
# program text — a directory containing a quote would otherwise either break the
# parse or execute whatever it contains.
python3 - "$DIR/media.json" "$DIR/meta.json" "$DIR/.video_url" <<'PY'
import json
import sys

raw = json.load(open(sys.argv[1], encoding="utf-8"))


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def num(value, cast, default=0):
    """Cast a field that the API sometimes returns as a formatted string."""
    if value is None:
        return default
    try:
        return cast(value)
    except (TypeError, ValueError):
        try:
            return cast(str(value).replace(" ", "").replace(",", "").replace(" ", ""))
        except (TypeError, ValueError):
            return default


video_url, meta = "", {}
for node in walk(raw):
    if not video_url:
        if isinstance(node.get("video_url"), str):
            video_url = node["video_url"]
        elif isinstance(node.get("video_versions"), list) and node["video_versions"]:
            first = node["video_versions"][0]
            if isinstance(first, dict):
                video_url = first.get("url", "")
    if not meta and node.get("pk") and node.get("code"):
        caption = node.get("caption")
        meta = {
            "code": node.get("code", ""),
            "pk": str(node["pk"]),
            "caption": caption.get("text", "") if isinstance(caption, dict) else (node.get("caption_text") or ""),
            "views": num(node.get("play_count") or node.get("view_count"), int),
            "likes": num(node.get("like_count"), int),
            "comments": num(node.get("comment_count"), int),
            "duration": num(node.get("video_duration"), float, 0.0),
            "taken_at": num(node.get("taken_at"), float, 0.0),
            "url": f"https://www.instagram.com/reel/{node.get('code', '')}/",
        }

meta["video_url_found"] = bool(video_url)
json.dump(meta, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(sys.argv[3], "w", encoding="utf-8").write(video_url)
PY

VIDEO_URL="$(cat "$DIR/.video_url")"
MEDIA_PK="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1],encoding="utf-8")).get("pk",""))' "$DIR/meta.json")"

# The raw response carries the same signed URL as .video_url. Keeping it would
# park a credential-bearing link in a folder the skill tells you to keep forever.
rm -f "$DIR/media.json"

if [ -z "$VIDEO_URL" ]; then
  log "no video url in the response (private, deleted, or not a video) — stopping after metadata"
  touch "$DIR/.no_video"
  exit 0
fi

# CDN links are signed and expire within hours. Download promptly; a 403 means
# the link went stale, so re-run this script rather than reusing the old URL.
log "downloading video"
curl -sSL "${CURL_FAIL[@]}" --max-time 180 -o "$DIR/video.mp4" "$VIDEO_URL"
rm -f "$DIR/.video_url"

log "storyboarding first 3 seconds at 0.5s intervals"
ffmpeg -nostdin -loglevel error -y -i "$DIR/video.mp4" -t 3 -vf "fps=2" "$DIR/frames/f_%02d.jpg"

log "extracting audio"
ffmpeg -nostdin -loglevel error -y -i "$DIR/video.mp4" -vn -ac 1 -ar 16000 -c:a libopus -b:a 64k "$DIR/audio.ogg"

if [ -n "${GROQ_API_KEY:-}" ]; then
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
else
  log "GROQ_API_KEY not set, skipping transcription (https://console.groq.com)"
fi

# The pk comes from parsed JSON; make sure it is a bare number before it becomes
# part of a URL.
if printf '%s' "$MEDIA_PK" | grep -Eq '^[0-9]+$'; then
  log "fetching comments"
  curl -sS "${CURL_FAIL[@]}" "${BASE_URL}/v2/media/comments?media_id=${MEDIA_PK}" \
    -H "accept: application/json" -H "x-access-key: ${HIKER_API_KEY}" \
    -o "$DIR/comments.json" || log "comments unavailable (may be disabled)"
else
  log "no usable media pk, skipping comments"
fi

# The video is the bulky part and is only needed to produce frames and audio.
# Keep it only if you plan to watch it: 300 reels is several gigabytes.
if [ "${KEEP_VIDEO:-0}" != "1" ]; then
  rm -f "$DIR/video.mp4"
  log "removed video.mp4 (set KEEP_VIDEO=1 to keep it)"
fi

log "done -> $DIR"
