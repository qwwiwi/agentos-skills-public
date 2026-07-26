#!/usr/bin/env python3
"""Fetch top-N reels per followed account within last N days.

Usage: python3 2-fetch-reels.py <output_dir> [--days 7] [--top 3] [--parallel 8]
Reads: <output_dir>/state/following.json, $HIKER_KEY (or $HIKER_API_KEY)
Writes: <output_dir>/state/reels-raw.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import urllib.request
import urllib.parse
import urllib.error

from _config import api_key

log = logging.getLogger("reel-radar.2")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("output_dir", type=Path)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--parallel", type=int, default=8)
    return p.parse_args()


async def fetch_clips(session_sem: asyncio.Semaphore, loop: asyncio.AbstractEventLoop,
                     user: dict, key: str, cutoff_ts: float, top: int) -> list[dict]:
    async with session_sem:
        try:
            clips = await loop.run_in_executor(None, _sync_fetch_clips, user["pk"], key)
        except Exception as e:
            log.warning("clips fetch failed for @%s: %s", user.get("username"), e)
            return []
    fresh = [c for c in clips if c["taken_at"] >= cutoff_ts]
    fresh.sort(key=lambda c: c["play_count"], reverse=True)
    return [{**c, "author": user["username"], "author_bio": user.get("biography", ""),
             "author_followers": user.get("follower_count", 0)} for c in fresh[:top]]


def _sync_fetch_clips(user_id: str, key: str) -> list[dict]:
    q = urllib.parse.urlencode({"user_id": user_id})
    req = urllib.request.Request(
        f"https://api.instagrapi.com/v2/user/clips?{q}",
        headers={"x-access-key": key},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8", errors="replace"))
    items = data.get("items") or data.get("response", {}).get("items") or []
    out: list[dict] = []
    for it in items:
        media = it.get("media") or it
        code = media.get("code", "")
        caption = (media.get("caption") or {}).get("text", "") if isinstance(media.get("caption"), dict) else (media.get("caption_text") or "")
        out.append({
            "code": code,
            "pk": str(media.get("pk") or media.get("id", "")),
            "caption": caption,
            "play_count": int(media.get("play_count") or media.get("view_count") or 0),
            "like_count": int(media.get("like_count") or 0),
            "comment_count": int(media.get("comment_count") or 0),
            "video_duration": float(media.get("video_duration") or 0),
            "taken_at": float(media.get("taken_at") or 0),
            "url": f"https://www.instagram.com/reel/{code}/" if code else "",
        })
    return out


async def main_async(args: argparse.Namespace) -> int:
    (args.output_dir / "state").mkdir(parents=True, exist_ok=True)
    key = api_key()

    following = json.loads((args.output_dir / "state" / "following.json").read_text())
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp()
    log.info("window cutoff: %s (%d days back)", datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat(), args.days)

    sem = asyncio.Semaphore(args.parallel)
    loop = asyncio.get_event_loop()
    tasks = [fetch_clips(sem, loop, u, key, cutoff, args.top) for u in following]
    results: list[list[dict]] = []
    for i, coro in enumerate(asyncio.as_completed(tasks), 1):
        try:
            r = await coro
            results.append(r)
        except Exception as e:
            log.warning("task %d failed: %s", i, e)
            results.append([])
        if i % 10 == 0:
            log.info("progress: %d/%d accounts", i, len(tasks))

    flat = [c for batch in results for c in batch]
    target = args.output_dir / "state" / "reels-raw.json"
    target.write_text(json.dumps(flat, ensure_ascii=False, indent=2))
    log.info("wrote %s (%d reels total)", target, len(flat))
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    sys.exit(main())
