#!/usr/bin/env python3
"""Fetch the reference account's OWN top-N reels over the last M days.

These are used as the relevance baseline: what already works on your own
channel, so the shortlist is matched against your audience, not a stranger's.

The account is NOT hardcoded: --username > $TARGET_USER > config/defaults.json.

Usage: python3 7-fetch-own-reels.py <output_dir> [--days 30] [--top 10] [--username <login>]
Writes: <output_dir>/state/own-reels.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _config import api_key, target_user

log = logging.getLogger("reel-radar.7")


def http_get(url: str, headers: dict[str, str]) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def fetch_user_id(username: str, key: str) -> str:
    data = http_get(
        f"https://api.instagrapi.com/v2/user/by/username?username={username}",
        {"x-access-key": key},
    )
    return str(data.get("user", {}).get("pk") or data.get("pk") or "")


def fetch_clips(user_id: str, key: str) -> list[dict]:
    q = urllib.parse.urlencode({"user_id": user_id})
    data = http_get(
        f"https://api.instagrapi.com/v2/user/clips?{q}",
        {"x-access-key": key},
    )
    return data.get("items") or data.get("response", {}).get("items") or []


def normalize(items: list[dict]) -> list[dict]:
    out = []
    for it in items:
        m = it.get("media") or it
        code = m.get("code", "")
        cap = m.get("caption")
        caption = cap.get("text", "") if isinstance(cap, dict) else (m.get("caption_text") or "")
        out.append({
            "code": code,
            "caption": caption,
            "play_count": int(m.get("play_count") or m.get("view_count") or 0),
            "like_count": int(m.get("like_count") or 0),
            "comment_count": int(m.get("comment_count") or 0),
            "taken_at": float(m.get("taken_at") or 0),
            "url": f"https://www.instagram.com/reel/{code}/" if code else "",
        })
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--username", default=None)
    args = ap.parse_args()

    key = api_key()
    username = target_user(args.username)

    uid = fetch_user_id(username, key)
    log.info("@%s user_id=%s", username, uid)

    items = normalize(fetch_clips(uid, key))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp()
    fresh = [x for x in items if x["taken_at"] >= cutoff]
    fresh.sort(key=lambda r: r["play_count"], reverse=True)
    top = fresh[: args.top]

    (args.output_dir / "state").mkdir(parents=True, exist_ok=True)
    target = args.output_dir / "state" / "own-reels.json"
    target.write_text(json.dumps(top, ensure_ascii=False, indent=2))
    log.info("wrote %s (%d own reels, top %d by views)", target, len(fresh), len(top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
