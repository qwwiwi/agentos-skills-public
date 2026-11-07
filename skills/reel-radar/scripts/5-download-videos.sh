#!/usr/bin/env bash
# Download top-25 reels via Loore ig-download (signed downloadUrl, 0.5 credits per file).
# Usage: 5-download-videos.sh <output_dir>
set -euo pipefail

OUT="${1:?usage: 5-download-videos.sh <output_dir>}"
: "${LOORE_API_KEY:?LOORE_API_KEY env var is required (https://docs.loore.ai)}"
THRESHOLD_MB="${COMPRESS_THRESHOLD_MB:-50}"
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"

STATE="$OUT/state/reels-top25.json"
VIDS="$OUT/videos"
[ -f "$STATE" ] || { echo "ERR: $STATE not found (run steps 1-4 first)" >&2; exit 2; }
mkdir -p "$VIDS"
echo "downloading reels from $STATE into $VIDS"

# The key stays in the environment, never argv -- argv is world-readable in `ps`.
PYTHONPATH="$SCRIPTS" python3 - "$STATE" "$VIDS" "$THRESHOLD_MB" <<'PYEOF'
import json, os, shutil, subprocess, sys, urllib.request

import _loore

state, vids, threshold_mb = sys.argv[1:4]
threshold_bytes = int(threshold_mb) * 1024 * 1024
reels = json.loads(open(state).read())
key = _loore.api_key()

for i, r in enumerate(reels, 1):
    code = r.get("code", "")
    if not code:
        print(f"[{i}] SKIP no code"); continue
    out = f"{vids}/{i}_{r.get('author','unknown')}_{code}.mp4"
    if os.path.exists(out) and os.path.getsize(out) > 0:
        print(f"[{i}] CACHED {out}"); continue

    url = r.get("url") or f"https://www.instagram.com/reel/{code}/"
    try:
        res = _loore.call("ig-download", {"url": url}, key=key)
        signed = res.get("downloadUrl", "")
        private = (res.get("artifact") or {}).get("url", "")
        if signed:
            # downloadUrl is key-free and lives ~15 minutes: fetch it right away.
            subprocess.check_call(["curl", "-sfL", "--max-time", "300", "-o", out, signed])
        elif private:
            # artifact.url needs the key as a Bearer header (kept out of argv).
            req = urllib.request.Request(private, headers={"Authorization": f"Bearer {key}"})
            with urllib.request.urlopen(req, timeout=300) as resp, open(out, "wb") as fh:
                shutil.copyfileobj(resp, fh)
        else:
            print(f"[{i}] NO_URL {code}"); continue
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
    except _loore.LooreError as e:
        if e.fatal and e.http_status != 403:
            print(f"[{i}] STOP {code}: {e.hint()}"); sys.exit(1)
        print(f"[{i}] FAIL {code}: {e}")
    except Exception as e:
        print(f"[{i}] FAIL {code}: {e}")
PYEOF
