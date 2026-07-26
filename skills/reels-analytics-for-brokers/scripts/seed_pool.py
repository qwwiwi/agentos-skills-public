#!/usr/bin/env python3
"""Step 1-2: build a candidate pool, filtering for free before spending money.

Sources (combine them, they overlap in useful ways):
  manual    — your hand-made seed list (the base you built yourself; see SKILL.md)
  following — SNOWBALL: who each seed account follows (the cheap multiplier)
  followers — subscribers of a reference account in the niche
  hashtag   — recent posts under niche hashtags
  search    — reels/accounts search by niche queries

The point of this script is the ORDER of operations. Listing endpoints hand back
username and full_name for free (they come inside the list payload), while the
bio only arrives from a paid per-profile call. So the crude keyword cut runs on
the free fields first and only survivors reach the paid step. On a real run that
turned a $37 brute-force sweep into a $0.06 one.

Usage:
  export HIKER_API_KEY=...
  python3 seed_pool.py --config config/niche.brokers.json --out runs/2026-07-26 \
      --sources manual,following,hashtag --seed-file manual-100.txt

Writes: <out>/pool.json, <out>/seed_stats.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from hiker import Hiker, paginate, unwrap

log = logging.getLogger("seed-pool")

DEFAULT_SOURCES = "manual,following,followers,hashtag,search"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a candidate account pool for a niche.")
    parser.add_argument("--config", type=Path, required=True, help="niche config JSON")
    parser.add_argument("--out", type=Path, required=True, help="run directory")
    parser.add_argument("--sources", default=DEFAULT_SOURCES, help=f"comma list, default: {DEFAULT_SOURCES}")
    parser.add_argument("--seed-file", type=Path, help="text file, one @username per line (your manual base)")
    parser.add_argument("--max-candidates", type=int, default=20000, help="stop scanning after this many raw candidates")
    parser.add_argument("--pages-per-source", type=int, default=10, help="pagination depth per listing call")
    parser.add_argument("--rps", type=float, default=6.0, help="requests per second cap")
    return parser.parse_args()


def normalise(text: str) -> str:
    """Lowercase and collapse separators so 'Риелтор_Мск' matches 'риелтор'."""
    return re.sub(r"[\s_.\-|/]+", " ", (text or "").lower())


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    """Return which keywords appear in the text (substring match)."""
    haystack = normalise(text)
    return [kw for kw in keywords if normalise(kw).strip() in haystack]


class Pool:
    """Deduplicating candidate store keyed by Instagram user id."""

    def __init__(self) -> None:
        self.items: dict[str, dict[str, Any]] = {}
        self.seen = 0
        self.rejected_negative = 0

    def add(self, user: dict[str, Any], source: str, keywords: list[str], negatives: list[str],
            free_filter: bool = True) -> bool:
        """Consider one candidate. Returns True if it entered the pool.

        ``free_filter=False`` is for the manual seed list and for accounts that
        surfaced because they already posted matching content — there the source
        itself is the evidence, so we do not re-litigate it on the username.
        """
        pk = str(user.get("pk") or user.get("id") or "")
        username = user.get("username") or ""
        if not pk or not username:
            return False
        self.seen += 1

        surface = f"{username} {user.get('full_name', '')}"
        if keyword_hits(surface, negatives):
            self.rejected_negative += 1
            return False

        hits = keyword_hits(surface, keywords)
        if free_filter and not hits:
            return False

        existing = self.items.get(pk)
        if existing:
            if source not in existing["sources"]:
                existing["sources"].append(source)
            existing["matched"] = sorted(set(existing["matched"]) | set(hits))
            return False

        self.items[pk] = {
            "pk": pk,
            "username": username,
            "full_name": user.get("full_name", ""),
            "is_private": bool(user.get("is_private", False)),
            "sources": [source],
            "matched": hits,
        }
        return True


def iter_users(payload_items: list[Any]) -> list[dict[str, Any]]:
    """Extract user objects out of a heterogeneous list payload."""
    users: list[dict[str, Any]] = []
    for item in payload_items:
        if not isinstance(item, dict):
            continue
        # Listing endpoints return users directly; media endpoints nest them.
        if item.get("username"):
            users.append(item)
        media = item.get("media") if isinstance(item.get("media"), dict) else item
        if isinstance(media, dict) and isinstance(media.get("user"), dict):
            users.append(media["user"])
    return users


def resolve_user_id(client: Hiker, username: str) -> str | None:
    """username -> numeric pk (one paid request)."""
    payload = client.get("/v2/user/by/username", {"username": username.lstrip("@")})
    user = unwrap(payload, "user") or payload.get("user") or payload
    pk = (user or {}).get("pk") or (user or {}).get("id")
    return str(pk) if pk else None


def harvest_listing(client: Hiker, pool: Pool, path: str, params: dict[str, Any], source: str,
                    keywords: list[str], negatives: list[str], pages: int, limit: int) -> None:
    """Walk a paginated listing endpoint and push every user through the free filter."""
    for page in paginate(client, path, params, ("users", "items", "response"), max_pages=pages):
        for user in iter_users(page):
            pool.add(user, source, keywords, negatives)
        if pool.seen >= limit:
            log.info("hit --max-candidates (%d), stopping %s", limit, source)
            return


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)

    keywords: list[str] = config.get("keywords_free", [])
    negatives: list[str] = config.get("negative_keywords", [])
    if not keywords:
        log.error("config has no 'keywords_free' — the free filter is the whole point, fill it in")
        return 2

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    client = Hiker(rps=args.rps)
    pool = Pool()

    seeds: list[str] = []
    if args.seed_file and args.seed_file.exists():
        seeds = [line.strip().lstrip("@") for line in args.seed_file.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.startswith("#")]
        log.info("manual seed list: %d accounts", len(seeds))
    elif "manual" in sources or "following" in sources:
        log.warning("no --seed-file given; the manual base is what makes this pipeline work (see SKILL.md)")

    # --- manual: your hand-built base goes in unconditionally -----------------
    if "manual" in sources:
        for username in seeds:
            pool.add({"pk": f"manual:{username}", "username": username, "full_name": ""},
                     "manual", keywords, negatives, free_filter=False)
        log.info("manual seeds added: %d", len(pool.items))

    # --- following: the snowball ---------------------------------------------
    # Each hand-picked account follows ~100 others in the same niche. Walking
    # those lists multiplies a curated hundred into thousands of candidates,
    # and the free filter keeps the paid step small.
    if "following" in sources and seeds:
        for i, username in enumerate(seeds, 1):
            try:
                user_id = resolve_user_id(client, username)
                if not user_id:
                    log.warning("cannot resolve @%s, skipping", username)
                    continue
                harvest_listing(client, pool, "/v2/user/following", {"user_id": user_id},
                                f"following:@{username}", keywords, negatives,
                                args.pages_per_source, args.max_candidates)
            except Exception as err:
                log.warning("following @%s failed: %s", username, err)
            if i % 10 == 0:
                log.info("snowball %d/%d seeds | pool=%d | requests=%d", i, len(seeds), len(pool.items),
                         client.requests_used)
            if pool.seen >= args.max_candidates:
                break

    # --- followers of reference accounts -------------------------------------
    if "followers" in sources:
        for username in config.get("reference_accounts", []):
            try:
                user_id = resolve_user_id(client, username)
                if not user_id:
                    continue
                harvest_listing(client, pool, "/v2/user/followers", {"user_id": user_id},
                                f"followers:@{username}", keywords, negatives,
                                args.pages_per_source, args.max_candidates)
            except Exception as err:
                log.warning("followers @%s failed: %s", username, err)

    # --- hashtags -------------------------------------------------------------
    if "hashtag" in sources:
        for tag in config.get("hashtags", []):
            try:
                info = client.get("/v2/hashtag/by/name", {"name": tag})
                hashtag_id = (unwrap(info, "id", "pk") or (info.get("hashtag") or {}).get("id"))
                if not hashtag_id:
                    log.warning("no id for #%s", tag)
                    continue
                for page in paginate(client, "/v2/hashtag/medias/recent", {"hashtag_id": hashtag_id},
                                     ("items", "sections", "response"), max_pages=args.pages_per_source):
                    for user in iter_users(page):
                        # Posting under a niche hashtag is itself the signal.
                        pool.add(user, f"hashtag:#{tag}", keywords, negatives, free_filter=False)
            except Exception as err:
                log.warning("hashtag #%s failed: %s", tag, err)

    # --- search ---------------------------------------------------------------
    if "search" in sources:
        for query in config.get("search_queries", []):
            for path in ("/v2/fbsearch/reels", "/v2/fbsearch/accounts"):
                try:
                    payload = client.get(path, {"query": query})
                    items = unwrap(payload, "items", "users", "reels") or []
                    for user in iter_users(items if isinstance(items, list) else []):
                        pool.add(user, f"search:{query}", keywords, negatives, free_filter=False)
                except Exception as err:
                    log.warning("search '%s' on %s failed: %s", query, path, err)

    candidates = sorted(pool.items.values(), key=lambda c: (-len(c["sources"]), c["username"]))
    (args.out / "pool.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    stats = {
        "candidates_seen": pool.seen,
        "passed_free_filter": len(candidates),
        "rejected_by_negative_keywords": pool.rejected_negative,
        "requests_used": client.requests_used,
        "estimated_cost_usd": round(client.spent_usd, 4),
        "sources": sources,
        "multi_source_hits": sum(1 for c in candidates if len(c["sources"]) > 1),
    }
    (args.out / "seed_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("seen=%d  passed=%d  requests=%d  ~$%.4f",
             pool.seen, len(candidates), client.requests_used, client.spent_usd)
    log.info("wrote %s", args.out / "pool.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
