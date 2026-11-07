#!/usr/bin/env bash
set -euo pipefail

# Instagram SuperPower -- Analyze Account via Loore (https://docs.loore.ai)
# Usage: bash analyze.sh <username> [top_N] [days]
# Example: bash analyze.sh someaccount 5 14
# Reads: $LOORE_API_KEY (required), $LOORE_SPEND_AUTHORIZATION_ID (user-approved spend budget)

USERNAME="${1:?Usage: analyze.sh <username> [top_N] [days]}"
TOP_N="${2:-5}"
DAYS="${3:-14}"

if [ -z "${LOORE_API_KEY:-}" ]; then
    echo "ERROR: LOORE_API_KEY is not set (create a key at https://app.loore.ai -> Настройки -> API и MCP)"
    exit 1
fi

echo "Analyzing @${USERNAME} -- top ${TOP_N} reels, last ${DAYS} days..."
echo ""

# The key stays in the environment: it is never interpolated into code or argv.
python3 - "$USERNAME" "$TOP_N" "$DAYS" <<'PYEOF'
import json, os, sys, urllib.error, urllib.request
from datetime import datetime, timezone, timedelta

username = sys.argv[1].lstrip("@")
top_n = int(sys.argv[2])
days = int(sys.argv[3])
key = os.environ["LOORE_API_KEY"]
spend_id = os.environ.get("LOORE_SPEND_AUTHORIZATION_ID", "").strip()
base = os.environ.get("LOORE_API_BASE", "https://mcp.loore.ai").rstrip("/")

HINTS = {
    401: "Loore key rejected -- check LOORE_API_KEY",
    402: "Loore credits or plan quota exhausted",
    403: "key has no access to this method, or the account is private",
    428: "spend approval needed -- create a budget: spend_authorization (see SKILL.md), then export LOORE_SPEND_AUTHORIZATION_ID",
    429: "Loore request budget exhausted -- retry later",
}

def api_post(method, body, paid=True):
    if paid and spend_id:
        body = {**body, "spend_authorization_id": spend_id}
    req = urllib.request.Request(
        f"{base}/v1/{method}",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            env = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error", "")
        except Exception:
            err = ""
        raise RuntimeError(f"{method}: HTTP {e.code} {err} -- {HINTS.get(e.code, 'Loore error')}") from None
    if env.get("status") != "ok":
        raise RuntimeError(f"{method}: {env.get('error', 'unknown error')}")
    return env.get("result") or {}

def fmt(n):
    return f"{n:,}" if isinstance(n, int) else "?"

# 1. Profile
print(f"Looking up @{username}...")
try:
    user = api_post("ig-profile", {"username": username}).get("profile") or {}
    user_id = user.get("id")
    print(f"Account: @{user.get('username', username)}")
    print(f"Full name: {user.get('fullName', '?')}")
    print(f"Followers: {fmt(user.get('followers'))}")
    print(f"Following: {fmt(user.get('following'))}")
    print(f"Posts: {fmt(user.get('posts'))}")
    print(f"Verified: {user.get('isVerified', '?')}")
    print(f"Category: {user.get('category', '?')}")
    print(f"Bio: {user.get('biography', '')[:100]}")
    print()
except Exception as e:
    print(f"Profile lookup failed: {e}")
    sys.exit(1)

# 2. Reels (newest first; pinned reels can be old and do not end the walk)
print(f"Fetching reels...")
cutoff = datetime.now(timezone.utc) - timedelta(days=days)
all_reels = []
cursor = None
subject = {"user_id": str(user_id)} if user_id else {"username": username}

for page in range(3):  # max 3 pages x 50 reels
    body = {**subject, "limit": 50, "include_caption": True}
    if cursor:
        body["cursor"] = cursor

    try:
        data = api_post("ig-user-reels", body)
    except Exception as e:
        print(f"Clips fetch error: {e}")
        break

    items = data.get("items") or []
    if not items:
        break

    oldest_in_page = None
    for media in items:
        taken = media.get("takenAt")
        if not taken:
            continue
        taken_dt = datetime.fromisoformat(taken.replace("Z", "+00:00"))
        if not media.get("isPinned"):
            oldest_in_page = taken_dt

        if taken_dt < cutoff:
            continue

        code = media.get("code", "")
        views = media.get("views") or 0
        likes = media.get("likes") or 0
        comments = media.get("comments") or 0
        caption = (media.get("caption") or "")[:200]

        all_reels.append({
            "code": code,
            "url": media.get("url") or f"https://www.instagram.com/reel/{code}/",
            "date": taken_dt.strftime("%Y-%m-%d"),
            "views": views,
            "likes": likes,
            "comments": comments,
            "caption": caption.replace("\n", " "),
            "engagement": views + likes * 10,
        })

    cursor = data.get("nextCursor")
    if not data.get("hasMore") or not cursor:
        break
    if oldest_in_page and oldest_in_page < cutoff:
        break

# 3. Sort and display
all_reels.sort(key=lambda r: r["engagement"], reverse=True)
top = all_reels[:top_n]

print(f"\nFound {len(all_reels)} reels in last {days} days")
print(f"TOP {len(top)} by engagement:\n")
print("=" * 70)

for i, r in enumerate(top, 1):
    print(f"\n#{i}")
    print(f"  URL: {r['url']}")
    print(f"  Date: {r['date']}")
    print(f"  Views: {r['views']:,}")
    print(f"  Likes: {r['likes']:,}")
    print(f"  Comments: {r['comments']:,}")
    print(f"  Caption: {r['caption'][:120]}")
    print(f"  Engagement: {r['engagement']:,}")

print("\n" + "=" * 70)
print("JSON:")
print(json.dumps(top, ensure_ascii=False, indent=2))

# 4. Balance (free call)
try:
    balance = api_post("billing-balance", {}, paid=False)
    print(f"\nLoore balance: {balance.get('creditsRemaining', '?')} credits left")
except Exception:
    pass
PYEOF

echo ""
echo "Done."
