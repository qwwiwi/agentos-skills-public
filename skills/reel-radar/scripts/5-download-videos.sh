#!/usr/bin/env bash
# Download top-25 reels via HikerAPI /v1/media/by/code → video_url.
# Usage: 5-download-videos.sh <output_dir>
set -euo pipefail

OUT="${1:?usage: 5-download-videos.sh <output_dir>}"
: "${HIKER_KEY:?HIKER_KEY env var is required}"
THRESHOLD_MB="${COMPRESS_THRESHOLD_MB:-50}"

STATE="$OUT/state/reels-top25.json"
VIDS="$OUT/videos"
mkdir -p "$VIDS"

python3 - "$STATE" "$VIDS" "$HIKER_KEY" "$THRESHOLD_MB" <<'PYEOF'
import json, os, subprocess, sys, urllib.request

state, vids, key, threshold_mb = sys.argv[1:5]
threshold_bytes = int(threshold_mb) * 1024 * 1024
reels = json.loads(open(state).read())

for i, r in enumerate(reels, 1):
    code = r.get("code", "")
    if not code:
        print(f"[{i}] SKIP no code"); continue
    out = f"{vids}/{i}_{r.get('author','unknown')}_{code}.mp4"
    if os.path.exists(out) and os.path.getsize(out) > 0:
        print(f"[{i}] CACHED {out}"); continue

    req = urllib.request.Request(
        f"https://api.instagrapi.com/v1/media/by/code?code={code}",
        headers={"x-access-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace").replace("\x00", "")
        data = json.loads(body)
        url = data.get("video_url") or data.get("video_versions", [{}])[0].get("url", "")
        if not url:
            print(f"[{i}] NO_URL {code}"); continue
        subprocess.check_call(["curl", "-sL", "--max-time", "300", "-o", out, url])
        size = os.path.getsize(out)
        if size > threshold_bytes:
            compressed = out.replace(".mp4", "_c.mp4")
            print(f"[{i}] COMPRESS {size//1024//1024}MB → {compressed}")
            subprocess.check_call([
                "ffmpeg", "-y", "-i", out,
                "-c:v", "libx264", "-preset", "fast", "-crf", "28",
                "-vf", "scale='min(720,iw)':-2",
                "-c:a", "aac", "-b:a", "96k", compressed,
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.replace(compressed, out)
        print(f"[{i}] OK {out} ({os.path.getsize(out)//1024}KB)")
    except Exception as e:
        print(f"[{i}] FAIL {code}: {e}")
PYEOF
