#!/usr/bin/env python3
"""Fetch the following list of the reference account via Loore (ig_following).

The account is NOT hardcoded: --username > $TARGET_USER > config/defaults.json.

Usage: python3 1-fetch-following.py <output_dir> [--username <login>]
Reads: $LOORE_API_KEY, optional $LOORE_SPEND_AUTHORIZATION_ID
Writes: <output_dir>/state/following.json
Cache:  <skill_root>/cache/following-<username>.json (TTL 24h)

Loore list rows carry no bio and no follower count (they are readable only via
ig_profile, one call per account). Step 2 fills both for the accounts that
actually posted in the window, so this step stays one cheap paginated walk.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

import _loore
from _config import SKILL_ROOT, api_key, load_config, target_user

CACHE_FILE = SKILL_ROOT / "cache" / "following.json"
# 50 rows per page is the contract maximum; 200 pages = up to 10 000 accounts.
PAGE_SIZE = 50
MAX_PAGES = 200


def _cache_ttl_seconds() -> int:
    """Cache lifetime: $CACHE_TTL_HOURS wins over config/defaults.json, default 24h."""
    raw = os.environ.get("CACHE_TTL_HOURS") or load_config().get("cache_ttl_hours", 24)
    try:
        hours = int(raw)
    except (TypeError, ValueError):
        hours = 24
    return (hours if hours > 0 else 24) * 3600


CACHE_TTL = _cache_ttl_seconds()

log = logging.getLogger("reel-radar.1")


def fetch_following(username: str, key: str) -> list[dict]:
    """Walk ig_following for one account and return pipeline-shaped rows.

    Args:
        username: reference account handle.
        key: Loore API key.

    Returns:
        Rows with pk, username, full_name, is_private; biography and
        follower_count stay empty until step 2 enriches them.
    """
    out: list[dict] = []
    seen: set[str] = set()
    body = {"username": username, "limit": PAGE_SIZE, "fields": "extended"}
    for u in _loore.paginate("ig-following", body, key=key, max_pages=MAX_PAGES):
        pk = str(u.get("id", ""))
        handle = u.get("username", "")
        ident = pk or handle
        if not ident or ident in seen:
            continue
        seen.add(ident)
        out.append(
            {
                "pk": pk,
                "username": handle,
                "full_name": u.get("fullName", ""),
                "biography": "",
                "is_private": bool(u.get("isPrivate", False)),
                "follower_count": 0,
            }
        )
    return out


def cache_file(username: str) -> Path:
    """One cache file per reference account, so switching accounts cannot serve stale data."""
    safe = "".join(c for c in username if c.isalnum() or c in "._-")
    return CACHE_FILE.parent / f"following-{safe}.json"


def load_cache(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > CACHE_TTL:
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def save_cache(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) < 2:
        log.error("usage: 1-fetch-following.py <output_dir> [--username <login>]")
        return 2
    out_dir = Path(sys.argv[1])
    (out_dir / "state").mkdir(parents=True, exist_ok=True)

    cli_user = None
    if "--username" in sys.argv:
        idx = sys.argv.index("--username")
        cli_user = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    username = target_user(cli_user)
    key = api_key()

    cache_path = cache_file(username)
    cached = load_cache(cache_path)
    if cached:
        log.info("cache hit: %d accounts", len(cached))
        following = cached
    else:
        log.info("fetching @%s following via Loore", username)
        try:
            following = fetch_following(username, key)
        except _loore.LooreError as e:
            log.error("%s", e.hint())
            return 1
        save_cache(cache_path, following)
        log.info("cached %d accounts", len(following))

    target = out_dir / "state" / "following.json"
    target.write_text(json.dumps(following, ensure_ascii=False, indent=2))
    log.info("wrote %s (%d accounts)", target, len(following))
    return 0


if __name__ == "__main__":
    sys.exit(main())
