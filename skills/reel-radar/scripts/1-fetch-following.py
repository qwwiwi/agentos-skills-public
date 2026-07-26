#!/usr/bin/env python3
"""Fetch the following list of the reference account via HikerAPI.

The account is NOT hardcoded: --username > $TARGET_USER > config/defaults.json.

Usage: python3 1-fetch-following.py <output_dir> [--username <login>]
Reads: $HIKER_KEY (or $HIKER_API_KEY)
Writes: <output_dir>/state/following.json
Cache:  <skill_root>/cache/following-<username>.json (TTL 24h)
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import urllib.request
import urllib.parse

from _config import SKILL_ROOT, api_key, target_user

CACHE_FILE = SKILL_ROOT / "cache" / "following.json"
CACHE_TTL = 24 * 3600

log = logging.getLogger("reel-radar.1")


def http_get(url: str, headers: dict[str, str]) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def fetch_user_id(username: str, key: str) -> str:
    data = http_get(
        f"https://api.instagrapi.com/v2/user/by/username?username={username}",
        {"x-access-key": key},
    )
    uid = data.get("user", {}).get("pk") or data.get("pk")
    if not uid:
        raise RuntimeError(f"user_id missing in response: {data}")
    return str(uid)


def fetch_following(user_id: str, key: str) -> list[dict]:
    out: list[dict] = []
    page_id = ""
    seen_pks: set[str] = set()
    while True:
        params = {"user_id": user_id}
        if page_id:
            params["page_id"] = page_id
        q = urllib.parse.urlencode(params)
        data = http_get(
            f"https://api.instagrapi.com/v2/user/following?{q}",
            {"x-access-key": key},
        )
        users = data.get("response", {}).get("users") or data.get("users") or []
        if not users:
            break
        new_count = 0
        for u in users:
            pk = str(u.get("pk", ""))
            if pk and pk in seen_pks:
                continue
            seen_pks.add(pk)
            new_count += 1
            out.append(
                {
                    "pk": pk,
                    "username": u.get("username", ""),
                    "full_name": u.get("full_name", ""),
                    "biography": u.get("biography", ""),
                    "is_private": u.get("is_private", False),
                    "follower_count": u.get("follower_count", 0),
                }
            )
        if new_count == 0:
            break
        next_id = data.get("next_page_id") or data.get("response", {}).get("next_max_id") or ""
        if not next_id or str(next_id) == str(page_id):
            break
        page_id = str(next_id)
        time.sleep(0.3)
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
        log.info("fetching @%s user_id", username)
        uid = fetch_user_id(username, key)
        log.info("user_id=%s, fetching following", uid)
        following = fetch_following(uid, key)
        save_cache(cache_path, following)
        log.info("cached %d accounts", len(following))

    target = out_dir / "state" / "following.json"
    target.write_text(json.dumps(following, ensure_ascii=False, indent=2))
    log.info("wrote %s (%d accounts)", target, len(following))
    return 0


if __name__ == "__main__":
    sys.exit(main())
