#!/usr/bin/env python3
"""Step 3: qualify pool candidates — paid profile check, then activity + reach.

This is the first step that spends real money (one ig-profile call per
candidate, 1 credit each), which is exactly why seed_pool.py already threw away
everything that failed the free username/full_name filter.

Two gates, cheapest first:
  1. Profile gate  — bio keywords, public account, follower floor.
     1 ig-profile call.
  2. Activity gate — enough reels inside the window. 1-2 ig-user-reels pages
     (with captions a page holds ~15-30 reels), only for accounts that
     survived gate 1.

Data source: Loore (https://docs.loore.ai).

An account that posts twice a quarter tells you nothing about what is working
right now, so the activity floor is not a nicety — it is what keeps the sample
made of people who are actually running the play.

Usage:
  export LOORE_API_KEY=...                      # app.loore.ai → Настройки → API и MCP
  export LOORE_SPEND_AUTHORIZATION_ID=...       # python3 scripts/loore.py approve ...
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

from loore import LooreError
from loore_ig import Client, media_fields, paginate
from seed_pool import keyword_hits, must_stop

log = logging.getLogger("qualify")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qualify candidate accounts by bio, activity and reach.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0, help="only process the first N candidates (0 = all)")
    parser.add_argument("--workers", type=int, default=6, help="parallel workers (the rate limiter still applies)")
    parser.add_argument("--clips-pages", type=int, default=2,
                        help="ig-user-reels pages per account (~15-30 reels per page with captions)")
    parser.add_argument("--rps", type=float, default=2.0, help="requests per second cap")
    return parser.parse_args()


def fetch_profile(client: Client, candidate: dict[str, Any]) -> dict[str, Any] | None:
    """Fetch the profile via ig-profile (1 credit).

    Manual seeds and hashtag/search authors arrive without a numeric id
    (``manual:`` / ``handle:`` keys) and are looked up by handle instead.

    Returns:
        Loore ``profile`` object (id, username, fullName, biography, category,
        followers, isPrivate, ...) or None when the account is gone.
    """
    pk = candidate["pk"]
    body = {"user_id": pk} if pk.isdigit() else {"username": candidate["username"]}
    profile = client.call("ig-profile", body).get("profile")
    return profile if isinstance(profile, dict) and profile.get("username") else None


def fetch_reels(client: Client, user_id: str, cutoff_ts: float, pages: int) -> list[dict[str, Any]]:
    """Fetch recent reels and keep the ones inside the window.

    Note: the feed starts with PINNED reels (``isPinned``), so it is not in
    chronological order. Never stop paginating at the first "old" item — read a
    fixed number of pages and filter by taken_at afterwards. Captions are asked
    for (capped at 500 characters per row) because offers_diff.py reads them.
    """
    collected: dict[str, dict[str, Any]] = {}
    body = {"user_id": user_id, "limit": 50, "include_caption": True}
    for page in paginate(client, "ig-user-reels", body, max_pages=pages):
        if not page:
            break
        for media in page:
            if isinstance(media, dict):
                reel = media_fields(media)
                # Keyed rather than appended: a repeated page would otherwise
                # inflate reels_in_window past the activity gate and drag the
                # median toward whichever reel got counted twice.
                identity = reel["pk"] or reel["code"]
                if identity:
                    collected[identity] = reel
    return [reel for reel in collected.values() if reel["taken_at"] >= cutoff_ts]


def qualify_one(client: Client, candidate: dict[str, Any], config: dict[str, Any],
                cutoff_ts: float, pages: int) -> dict[str, Any]:
    """Run both gates on one candidate and return a verdict record."""
    verdict: dict[str, Any] = {"username": candidate["username"], "passed": False, "reason": ""}

    profile = fetch_profile(client, candidate)
    if not profile:
        verdict["reason"] = "profile_not_found"
        return verdict

    bio = profile.get("biography", "") or ""
    full_name = profile.get("fullName", "") or ""
    surface = f"{profile.get('username', '')} {full_name} {bio} {profile.get('category', '') or ''}"
    if keyword_hits(surface, config.get("negative_keywords", [])):
        verdict["reason"] = "negative_keyword"
        return verdict

    bio_keywords = config.get("keywords_bio") or config.get("keywords_free", [])
    hits = keyword_hits(surface, bio_keywords)
    if not hits and "manual" not in candidate.get("sources", []):
        verdict["reason"] = "no_bio_keyword"
        return verdict

    followers = int(profile.get("followers") or 0)
    if followers < int(config.get("min_followers", 0)):
        verdict["reason"] = "below_follower_floor"
        return verdict
    if profile.get("isPrivate"):
        verdict["reason"] = "private"
        return verdict

    user_id = str(profile.get("id") or "")
    if not user_id.isdigit():
        verdict["reason"] = "profile_without_id"
        return verdict
    reels = fetch_reels(client, user_id, cutoff_ts, pages)
    min_reels = int(config.get("min_reels_in_window", 10))
    if len(reels) < min_reels:
        verdict["reason"] = f"low_activity({len(reels)}<{min_reels})"
        return verdict

    # Loore flags a pinned old hit and a trial reel (shown to non-followers
    # only); both describe a different audience, so neither shapes the median.
    views = [r["views"] for r in reels if r["views"] > 0 and not r["is_pinned"] and not r["is_trial"]]
    median_views = statistics.median(views) if views else 0.0

    verdict.update({
        "passed": True,
        "reason": "ok",
        "account": {
            "pk": user_id,
            "username": profile.get("username", ""),
            "full_name": full_name,
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

    # Deduplicate BEFORE dispatching: the post-hoc check further down protects
    # the report, but by then both copies have already burned a paid profile
    # call plus up to three clip pages. Username is the only key both a manual
    # seed and a snowball hit share.
    unique: dict[str, dict[str, Any]] = {}
    for candidate in pool:
        unique.setdefault(candidate["username"].lower(), candidate)
    if len(unique) < len(pool):
        log.info("pool had %d duplicate entries, collapsed before spending", len(pool) - len(unique))
    pool = list(unique.values())

    if args.limit:
        pool = pool[: args.limit]

    window_days = int(config.get("window_days", 30))
    cutoff_ts = (datetime.now(timezone.utc) - timedelta(days=window_days)).timestamp()
    log.info("qualifying %d candidates | window=%dd | cutoff=%s",
             len(pool), window_days, datetime.fromtimestamp(cutoff_ts, tz=timezone.utc).date())

    client = Client(rps=args.rps)
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
                if must_stop(err):
                    # Key, credits or spend approval: every other call would be
                    # refused the same way, so stop instead of burning through.
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
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
                log.info("progress %d/%d | qualified=%d | requests=%d | credits=%.1f",
                         i, len(pool), len(accounts), client.requests_used, client.credits_charged)

    accounts.sort(key=lambda a: a["median_views"], reverse=True)
    (args.out / "accounts.json").write_text(json.dumps(accounts, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "reels.json").write_text(json.dumps(reels, ensure_ascii=False, indent=2), encoding="utf-8")

    stats = {
        "candidates_processed": len(pool),
        "qualified": len(accounts),
        "reels_collected": len(reels),
        "rejection_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "requests_used": client.requests_used,
        "credits_charged": round(client.credits_charged, 3),
        "window_days": window_days,
    }
    (args.out / "qualify_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("qualified=%d of %d | reels=%d | requests=%d | credits=%.1f",
             len(accounts), len(pool), len(reels), client.requests_used, client.credits_charged)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LooreError as err:
        # A rejected key, empty balance or missing spend approval. The
        # troubleshooting table promises a readable line, not a stack trace.
        print(err.hint(), file=sys.stderr)
        sys.exit(2)
