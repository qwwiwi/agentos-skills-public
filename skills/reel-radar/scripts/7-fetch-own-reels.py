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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import _loore
from _config import api_key, reel_row, target_user

log = logging.getLogger("reel-radar.7")

# 50 is the ig_user_reels page maximum; at most this many pages are read.
PAGE_SIZE = 50
MAX_PAGES = 3


def fetch_clips(username: str, key: str, cutoff_ts: float) -> list[dict]:
    """Read the account's reels newest-first until the window ends.

    Pinned and trial reels are left out: a pin is usually an old hit and a
    trial was shown to non-followers only, so neither describes the baseline.
    """
    out: list[dict] = []
    body = {"username": username, "limit": PAGE_SIZE, "include_caption": True}
    for it in _loore.paginate("ig-user-reels", body, key=key, max_pages=MAX_PAGES):
        if it.get("isPinned") or it.get("isTrial") or not it.get("code"):
            continue
        row = reel_row(it)
        if row["taken_at"] and row["taken_at"] < cutoff_ts:
            break
        out.append(row)
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

    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp()
    try:
        items = fetch_clips(username, key, cutoff)
    except _loore.LooreError as e:
        log.error("%s", e.hint())
        return 1
    log.info("@%s: %d reels read", username, len(items))
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
