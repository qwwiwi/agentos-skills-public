#!/usr/bin/env python3
"""Fetch top-N reels per followed account within last N days via Loore.

Per account: one ig_user_reels page (latest reels with views/likes/comments and
caption). Accounts with at least one reel in the window get one ig_profile call
for bio and follower count (ig_following rows do not carry them); accounts
without fresh reels cost no profile call. Private accounts are skipped.

Usage: python3 2-fetch-reels.py <output_dir> [--days 7] [--top 3] [--parallel 8]
Reads: <output_dir>/state/following.json, $LOORE_API_KEY, optional $LOORE_SPEND_AUTHORIZATION_ID
Writes: <output_dir>/state/reels-raw.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import _loore
from _config import api_key, reel_row

log = logging.getLogger("reel-radar.2")

# One page of the latest reels; a 7-day window rarely holds more.
REELS_PER_ACCOUNT = 20


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("output_dir", type=Path)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--parallel", type=int, default=8)
    return p.parse_args()


def _subject(user: dict) -> dict:
    """Address an account by id when known (cheaper), else by handle."""
    return {"user_id": user["pk"]} if user.get("pk") else {"username": user["username"]}


def _sync_fetch_clips(user: dict, key: str) -> list[dict]:
    result = _loore.call(
        "ig-user-reels",
        {**_subject(user), "limit": REELS_PER_ACCOUNT, "include_caption": True},
        key=key,
    )
    return [reel_row(it) for it in result.get("items") or [] if it.get("code")]


def _sync_fetch_profile(user: dict, key: str) -> dict:
    result = _loore.call("ig-profile", _subject(user), key=key)
    return result.get("profile") or {}


async def fetch_clips(session_sem: asyncio.Semaphore, loop: asyncio.AbstractEventLoop,
                     user: dict, key: str, cutoff_ts: float, top: int) -> list[dict]:
    """Return the account's top reels in the window, enriched with bio and followers."""
    if user.get("is_private"):
        return []
    async with session_sem:
        try:
            clips = await loop.run_in_executor(None, _sync_fetch_clips, user, key)
        except _loore.LooreError as e:
            if e.fatal and e.http_status != 403:
                raise
            log.warning("clips fetch failed for @%s: %s", user.get("username"), e)
            return []
    fresh = [c for c in clips if c["taken_at"] >= cutoff_ts]
    if not fresh:
        return []
    fresh.sort(key=lambda c: c["play_count"], reverse=True)
    bio, followers = user.get("biography", ""), int(user.get("follower_count") or 0)
    if not bio and not followers:
        async with session_sem:
            try:
                prof = await loop.run_in_executor(None, _sync_fetch_profile, user, key)
                bio, followers = prof.get("biography", ""), int(prof.get("followers") or 0)
            except _loore.LooreError as e:
                if e.fatal and e.http_status != 403:
                    raise
                log.warning("profile fetch failed for @%s: %s", user.get("username"), e)
    return [{**c, "author": user["username"], "author_bio": bio,
             "author_followers": followers} for c in fresh[:top]]


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
        except _loore.LooreError as e:
            if e.fatal:
                log.error("%s", e.hint())
                return 1
            log.warning("task %d failed: %s", i, e)
            results.append([])
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
