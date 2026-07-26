#!/usr/bin/env python3
"""Step 3: qualify pool candidates — paid profile check, then activity + reach.

This is the first step that spends real money (one profile call per candidate),
which is exactly why seed_pool.py already threw away everything that failed the
free username/full_name filter.

Two gates, cheapest first:
  1. Profile gate  — bio keywords, public account, follower floor. 1 request.
  2. Activity gate — enough reels inside the window. ~2-3 requests, only for
     accounts that survived gate 1.

An account that posts twice a quarter tells you nothing about what is working
right now, so the activity floor is not a nicety — it is what keeps the sample
made of people who are actually running the play.

Usage:
  export HIKER_API_KEY=...
  python3 qualify_accounts.py --config config/niche.brokers.json --out runs/2026-07-26

Reads:  <out>/pool.json
Writes: <out>/accounts.json, <out>/reels.json, <out>/qualify_stats.json
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from hiker import Hiker, media_fields, paginate, unwrap
from seed_pool import keyword_hits

log = logging.getLogger("qualify")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qualify candidate accounts by bio, activity and reach.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0, help="only process the first N candidates (0 = all)")
    parser.add_argument("--workers", type=int, default=6, help="parallel workers (the rate limiter still applies)")
    parser.add_argument("--clips-pages", type=int, default=3, help="clip pages per account (~12 reels per page)")
    parser.add_argument("--rps", type=float, default=6.0)
    return parser.parse_args()


def fetch_profile(client: Hiker, candidate: dict[str, Any]) -> dict[str, Any] | None:
    """Fetch the full profile. Manual seeds arrive without a numeric id."""
    pk = candidate["pk"]
    if pk.startswith("manual:"):
        payload = client.get("/v2/user/by/username", {"username": candidate["username"]})
    else:
        payload = client.get("/v2/user/by/id", {"id": pk})
    user = unwrap(payload, "user") or payload.get("user") or payload
    return user if isinstance(user, dict) and user.get("username") else None


def fetch_reels(client: Hiker, user_id: str, cutoff_ts: float, pages: int) -> list[dict[str, Any]]:
    """Fetch recent reels and keep the ones inside the window.

    Note: the clips endpoint returns PINNED reels first, so the feed is not in
    chronological order. Never stop paginating at the first "old" item — read a
    fixed number of pages and filter by taken_at afterwards.
    """
    collected: list[dict[str, Any]] = []
    for page in paginate(client, "/v2/user/clips", {"user_id": user_id}, ("items", "response"), max_pages=pages):
        if not page:
            break
        for item in page:
            media = item.get("media") if isinstance(item, dict) and isinstance(item.get("media"), dict) else item
            if isinstance(media, dict):
                collected.append(media_fields(media))
    return [reel for reel in collected if reel["taken_at"] >= cutoff_ts]


def qualify_one(client: Hiker, candidate: dict[str, Any], config: dict[str, Any],
                cutoff_ts: float, pages: int) -> dict[str, Any]:
    """Run both gates on one candidate and return a verdict record."""
    verdict: dict[str, Any] = {"username": candidate["username"], "passed": False, "reason": ""}

    profile = fetch_profile(client, candidate)
    if not profile:
        verdict["reason"] = "profile_not_found"
        return verdict

    bio = profile.get("biography", "") or ""
    surface = f"{profile.get('username', '')} {profile.get('full_name', '')} {bio} {profile.get('category', '') or ''}"
    if keyword_hits(surface, config.get("negative_keywords", [])):
        verdict["reason"] = "negative_keyword"
        return verdict

    bio_keywords = config.get("keywords_bio") or config.get("keywords_free", [])
    hits = keyword_hits(surface, bio_keywords)
    if not hits and "manual" not in candidate.get("sources", []):
        verdict["reason"] = "no_bio_keyword"
        return verdict

    followers = int(profile.get("follower_count") or 0)
    if followers < int(config.get("min_followers", 0)):
        verdict["reason"] = "below_follower_floor"
        return verdict
    if profile.get("is_private"):
        verdict["reason"] = "private"
        return verdict

    user_id = str(profile.get("pk") or profile.get("id") or "")
    reels = fetch_reels(client, user_id, cutoff_ts, pages)
    min_reels = int(config.get("min_reels_in_window", 10))
    if len(reels) < min_reels:
        verdict["reason"] = f"low_activity({len(reels)}<{min_reels})"
        return verdict

    views = [r["views"] for r in reels if r["views"] > 0]
    median_views = statistics.median(views) if views else 0.0

    verdict.update({
        "passed": True,
        "reason": "ok",
        "account": {
            "pk": user_id,
            "username": profile.get("username", ""),
            "full_name": profile.get("full_name", ""),
            "biography": bio,
            "followers": followers,
            "reels_in_window": len(reels),
            "median_views": round(median_views, 1),
            # How far the account's normal reel travels relative to its own
            # audience. Below ~1.0 the account only reaches its own followers.
            "reach_ratio": round(median_views / followers, 3) if followers else 0.0,
            "matched_keywords": hits,
            "sources": candidate.get("sources", []),
            "url": f"https://www.instagram.com/{profile.get('username', '')}/",
        },
        "reels": [dict(reel, account=profile.get("username", "")) for reel in reels],
    })
    return verdict


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    pool = json.loads((args.out / "pool.json").read_text(encoding="utf-8"))
    if args.limit:
        pool = pool[: args.limit]

    window_days = int(config.get("window_days", 30))
    cutoff_ts = (datetime.now(timezone.utc) - timedelta(days=window_days)).timestamp()
    log.info("qualifying %d candidates | window=%dd | cutoff=%s",
             len(pool), window_days, datetime.fromtimestamp(cutoff_ts, tz=timezone.utc).date())

    client = Hiker(rps=args.rps)
    accounts: list[dict[str, Any]] = []
    reels: list[dict[str, Any]] = []
    reasons: dict[str, int] = {}
    # Manual seeds enter the pool keyed by username (their numeric id is unknown
    # at seeding time), so the same account can also arrive through the snowball
    # under its real id. Both resolve to one profile here — dedupe on the id or
    # the account lands in the report twice and skews every aggregate.
    seen_ids: set[str] = set()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(qualify_one, client, c, config, cutoff_ts, args.clips_pages): c for c in pool}
        for i, future in enumerate(as_completed(futures), 1):
            candidate = futures[future]
            try:
                verdict = future.result()
            except Exception as err:
                log.warning("@%s failed: %s", candidate["username"], err)
                reasons["error"] = reasons.get("error", 0) + 1
                continue
            reasons[verdict["reason"]] = reasons.get(verdict["reason"], 0) + 1
            if verdict["passed"]:
                account_id = verdict["account"]["pk"]
                if account_id in seen_ids:
                    reasons["duplicate"] = reasons.get("duplicate", 0) + 1
                    continue
                seen_ids.add(account_id)
                accounts.append(verdict["account"])
                reels.extend(verdict["reels"])
            if i % 25 == 0:
                log.info("progress %d/%d | qualified=%d | requests=%d (~$%.3f)",
                         i, len(pool), len(accounts), client.requests_used, client.spent_usd)

    accounts.sort(key=lambda a: a["median_views"], reverse=True)
    (args.out / "accounts.json").write_text(json.dumps(accounts, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "reels.json").write_text(json.dumps(reels, ensure_ascii=False, indent=2), encoding="utf-8")

    stats = {
        "candidates_processed": len(pool),
        "qualified": len(accounts),
        "reels_collected": len(reels),
        "rejection_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "requests_used": client.requests_used,
        "estimated_cost_usd": round(client.spent_usd, 4),
        "window_days": window_days,
    }
    (args.out / "qualify_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("qualified=%d of %d | reels=%d | requests=%d (~$%.3f)",
             len(accounts), len(pool), len(reels), client.requests_used, client.spent_usd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
