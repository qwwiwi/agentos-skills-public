#!/usr/bin/env python3
"""Step 1-2: build a candidate pool, filtering for free before spending money.

Sources (combine them, they overlap in useful ways):
  manual    — your hand-made seed list (the base you built yourself; see SKILL.md)
  following — SNOWBALL: who each seed account follows (the cheap multiplier)
  followers — subscribers of a reference account in the niche
  hashtag   — recent posts under niche hashtags
  search    — reels/accounts search by niche queries

Data source: Loore (https://docs.loore.ai) — ig-following / ig-followers
(fields=extended for the display name), ig-hashtag-media, ig-search.

The point of this script is the ORDER of operations. Listing pages hand back
username and full_name inside the page itself, while the bio only arrives from
ig-profile, 1 credit per account. So the crude keyword cut runs on the list
fields first and only survivors reach the per-profile step. On a real run that
turned a 36 929-call brute-force sweep into 63 calls.

Hashtag and reel-search rows name only the author's handle (no id, no display
name). Those authors enter the pool keyed as ``handle:<username>`` and get
their numeric id in qualify_accounts.py.

Usage:
  export LOORE_API_KEY=...                      # app.loore.ai → Настройки → API и MCP
  export LOORE_SPEND_AUTHORIZATION_ID=...       # python3 scripts/loore.py approve ...
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

from loore import LooreError
from loore_ig import Client, paginate

log = logging.getLogger("seed-pool")

DEFAULT_SOURCES = "manual,following,followers,hashtag,search"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a candidate account pool for a niche.")
    parser.add_argument("--config", type=Path, required=True, help="niche config JSON")
    parser.add_argument("--out", type=Path, required=True, help="run directory")
    parser.add_argument("--sources", default=DEFAULT_SOURCES, help=f"comma list, default: {DEFAULT_SOURCES}")
    parser.add_argument("--seed-file", type=Path, help="text file, one @username per line (your manual base)")
    parser.add_argument("--max-candidates", type=int, default=20000, help="stop scanning after this many raw candidates")
    parser.add_argument("--pages-per-source", type=int, default=10,
                        help="pagination depth per listing call (up to 50 rows per page)")
    parser.add_argument("--rps", type=float, default=2.0, help="requests per second cap")
    return parser.parse_args()


def normalise(text: str) -> str:
    """Lowercase and collapse separators so 'Риелтор_Мск' matches 'риелтор'."""
    return re.sub(r"[\s_.\-|/]+", " ", (text or "").lower())


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    """Return which keywords appear in the text (substring match).

    A trailing space in a config keyword is meaningful: `"жк "` is written that
    way to mean "the word ЖК", not "anything starting with ЖК" (which would drag
    in ЖКХ). The haystack is padded so that boundary still matches at the very
    end of a name.
    """
    haystack = f" {normalise(text)} "
    return [kw for kw in keywords if normalise(kw) in haystack]


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
        hits = keyword_hits(surface, keywords)

        if free_filter:
            # Negative keywords only police accounts that the machine proposed.
            # A hand-picked seed is the user's judgement and outranks the filter:
            # a broker who also mentions renovations is still a broker, and
            # silently deleting him from the base he spent an evening building
            # would undermine the whole point of collecting it by hand.
            if keyword_hits(surface, negatives):
                self.rejected_negative += 1
                return False
            if not hits:
                return False
        elif keyword_hits(surface, negatives):
            log.info("keeping @%s despite a negative keyword (came from %s)", username, source)

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


def iter_users(rows: list[Any]) -> list[dict[str, Any]]:
    """Map Loore list rows to the pool's user shape.

    Account rows (ig-following, ig-followers, ig-search kind=accounts) carry
    ``username``, ``id``, ``isPrivate`` and, under fields=extended, ``fullName``.
    Media rows (ig-hashtag-media, ig-search kind=reels) carry only the author's
    handle in ``author``; such a user is keyed ``handle:<username>`` until
    qualification resolves the numeric id.

    Args:
        rows: One page of Loore rows.

    Returns:
        Dicts with ``pk``, ``username``, ``full_name``, ``is_private``.
    """
    users: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("username"):
            users.append({
                "pk": str(row.get("id") or f"handle:{row['username']}"),
                "username": str(row["username"]),
                "full_name": str(row.get("fullName") or ""),
                "is_private": bool(row.get("isPrivate", False)),
            })
        elif row.get("author"):
            author = str(row["author"]).lstrip("@")
            users.append({"pk": f"handle:{author}", "username": author, "full_name": "", "is_private": False})
    return users


def must_stop(err: Exception) -> bool:
    """True for refusals that end the whole run (key, credits, spend approval).

    A 403 is left per-source: it usually means that one account is private.
    """
    return isinstance(err, LooreError) and err.fatal and err.http_status != 403


def harvest_listing(client: Client, pool: Pool, method: str, body: dict[str, Any], source: str,
                    keywords: list[str], negatives: list[str], pages: int, limit: int) -> None:
    """Walk a paginated Loore listing and push every user through the free filter."""
    for page in paginate(client, method, {**body, "limit": 50}, max_pages=pages):
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
    client = Client(rps=args.rps)
    pool = Pool()

    seeds: list[str] = []
    if args.seed_file and args.seed_file.exists():
        seeds = [line.strip().lstrip("@") for line in args.seed_file.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.strip().startswith("#")]
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
    # and the free filter keeps the paid step small. The walk starts by handle
    # (no separate id lookup) and continues by the accountId Loore returns.
    if "following" in sources and seeds:
        for i, username in enumerate(seeds, 1):
            try:
                harvest_listing(client, pool, "ig-following", {"username": username, "fields": "extended"},
                                f"following:@{username}", keywords, negatives,
                                args.pages_per_source, args.max_candidates)
            except Exception as err:
                if must_stop(err):
                    raise
                log.warning("following @%s failed: %s", username, err)
            if i % 10 == 0:
                log.info("snowball %d/%d seeds | pool=%d | requests=%d | credits=%.1f", i, len(seeds),
                         len(pool.items), client.requests_used, client.credits_charged)
            if pool.seen >= args.max_candidates:
                break

    # --- followers of reference accounts -------------------------------------
    if "followers" in sources and pool.seen < args.max_candidates:
        for username in config.get("reference_accounts", []):
            try:
                harvest_listing(client, pool, "ig-followers", {"username": username, "fields": "extended"},
                                f"followers:@{username}", keywords, negatives,
                                args.pages_per_source, args.max_candidates)
            except Exception as err:
                if must_stop(err):
                    raise
                log.warning("followers @%s failed: %s", username, err)

    # --- hashtags -------------------------------------------------------------
    if "hashtag" in sources and pool.seen < args.max_candidates:
        for tag in config.get("hashtags", []):
            try:
                for page in paginate(client, "ig-hashtag-media", {"hashtag": tag, "rank": "recent", "limit": 50},
                                     max_pages=args.pages_per_source):
                    for user in iter_users(page):
                        # Posting under a niche hashtag is itself the signal.
                        pool.add(user, f"hashtag:#{tag}", keywords, negatives, free_filter=False)
            except Exception as err:
                if must_stop(err):
                    raise
                log.warning("hashtag #%s failed: %s", tag, err)

    # --- search ---------------------------------------------------------------
    if "search" in sources and pool.seen < args.max_candidates:
        for query in config.get("search_queries", []):
            for kind in ("reels", "accounts"):
                try:
                    result = client.call("ig-search", {"kind": kind, "query": query, "limit": 50,
                                                       "fields": "extended"})
                    items = result.get("items")
                    for user in iter_users(items if isinstance(items, list) else []):
                        pool.add(user, f"search:{query}", keywords, negatives, free_filter=False)
                except Exception as err:
                    if must_stop(err):
                        raise
                    log.warning("search '%s' (kind=%s) failed: %s", query, kind, err)

    # A manual seed (and a hashtag/search author) enters keyed by username — its
    # numeric id is unknown until a paid lookup — while the snowball finds the
    # same person keyed by pk. Left
    # alone they are two pool entries: the funnel double-counts, the multi-source
    # ranking never credits manual+following, and qualification pays twice for
    # one account. Merging on username here costs nothing and fixes all three.
    merged: dict[str, dict[str, Any]] = {}
    for candidate in pool.items.values():
        key = candidate["username"].lower()
        existing = merged.get(key)
        if not existing:
            merged[key] = candidate
            continue
        existing["sources"] = sorted(set(existing["sources"]) | set(candidate["sources"]))
        existing["matched"] = sorted(set(existing["matched"]) | set(candidate["matched"]))
        # Prefer the numeric id — it saves a lookup and never goes stale.
        if not existing["pk"].isdigit() and candidate["pk"].isdigit():
            existing["pk"] = candidate["pk"]
            existing["full_name"] = candidate["full_name"] or existing["full_name"]

    candidates = sorted(merged.values(), key=lambda c: (-len(c["sources"]), c["username"]))
    (args.out / "pool.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    stats = {
        "candidates_seen": pool.seen,
        "passed_free_filter": len(candidates),
        "merged_duplicates": len(pool.items) - len(candidates),
        "rejected_by_negative_keywords": pool.rejected_negative,
        "requests_used": client.requests_used,
        "credits_charged": round(client.credits_charged, 3),
        "sources": sources,
        "multi_source_hits": sum(1 for c in candidates if len(c["sources"]) > 1),
    }
    (args.out / "seed_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("seen=%d  passed=%d  requests=%d  credits=%.1f",
             pool.seen, len(candidates), client.requests_used, client.credits_charged)
    log.info("wrote %s", args.out / "pool.json")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LooreError as err:
        # A rejected key, empty balance or missing spend approval. The
        # troubleshooting table promises a readable line, not a stack trace.
        print(err.hint(), file=sys.stderr)
        sys.exit(2)
