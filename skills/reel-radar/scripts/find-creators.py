#!/usr/bin/env python3
"""Discover English-language IG creators posting >=30 reels/month about AI agents.

Pipeline (all data via Loore, https://docs.loore.ai):
  1. Discovery  -- ig_search kind=reels across many keywords (paginated) + ig_hashtag_media rank=reels
                   + optional watchlist seed => pool of candidate usernames with topic-hit tally
  2. Enrich     -- ig_profile by username => followers, id, bio; gate followers>=10k, public
  3. Cadence    -- one ig_user_reels page/account => reels_per_month from batch span; topic + english + recency gates
  4. Output     -- strict passes + ranked top-100 -> JSON + readable txt

Every page and every profile is a paid Loore request: set LOORE_SPEND_AUTHORIZATION_ID to a
budget the user approved (python3 _loore.py approve --flow find-creators --cap <credits>).
Single reels page/account (CADENCE_PAGE rows), so monthly cadence is extrapolated from the span of the batch.
Search rows carry no caption text, only the caption's hashtags -- those feed the topic tally.

Usage: LOORE_API_KEY=... python3 find-creators.py <out_dir> [--target 100] [--min-followers 10000]
                                                          [--min-reels-month 30] [--pages 3] [--parallel 8]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import _loore
from _config import iso_to_epoch

log = logging.getLogger("find-creators")

# Rows per search/hashtag page (contract maximum 50) and per cadence read.
PAGE_SIZE = 50
CADENCE_PAGE = 24

# EXAMPLE NICHE: AI / agents / coding. Replace all three lists below with the
# vocabulary of your own niche -- the rest of the script does not know the topic.
# Keep terms broad and IG-clean; avoid words that collide with big brands.
KEYWORDS = [
    "claude code", "claude ai", "claude code agent", "claude code workflow",
    "codex", "openai codex", "anthropic", "anthropic claude",
    "ai agents", "ai agent", "agentic ai", "agentic workflow",
    "autonomous agents", "llm agents", "ai automation", "ai coding",
    "vibe coding", "cursor ai", "mcp server", "build ai agent",
    "github copilot", "ai developer", "ai workflow", "prompt engineering",
    "claude skills", "n8n automation",
    # batch 2 -- broaden reach to push strict count toward target
    "chatgpt", "ai tools", "ai news", "make automation", "zapier ai",
    "no code ai", "ai saas", "ai for business", "perplexity ai", "gemini ai",
    "ai influencer", "coding tips", "software engineer", "build in public",
    "indie hacker", "ai tutorial", "ai startup", "future of ai", "ai tips",
    "ai content", "automation agency", "ai marketing", "tech tips ai",
    "ai productivity", "machine learning", "ai app", "ai voice agent",
    "ai chatbot", "claude desktop", "ai engineer",
]

HASHTAGS = [
    "claudecode", "aiagents", "aiagent", "vibecoding", "anthropic",
    "codex", "agenticai", "aiautomation", "mcp", "cursorai",
    "aitools", "buildinpublic", "aicoding", "claudeai", "llm",
    "promptengineering", "aiworkflow", "n8n", "aideveloper", "openai",
    "automationagency", "aibuilder", "chatgpt", "aiengineer",
]

# Topic relevance: at least one hit in bio+name+captions to keep.
TOPIC_TERMS = [
    "claude", "codex", "anthropic", "agent", "agentic", "llm", "mcp",
    "ai automation", "automation", "cursor", "vibe", "gpt", "prompt",
    "copilot", "openai", "n8n", "ai coding", "ai tool", "ai workflow",
    "ai builder",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("out_dir", type=Path)
    p.add_argument("--target", type=int, default=100)
    p.add_argument("--min-followers", type=int, default=10_000)
    p.add_argument("--min-reels-month", type=int, default=30)
    p.add_argument("--pages", type=int, default=3)
    p.add_argument("--parallel", type=int, default=8)
    return p.parse_args()


def _caption_text(m: dict) -> str:
    """Caption when the row carries it, otherwise its hashtags as '#tag' words."""
    return m.get("caption") or " ".join(f"#{t}" for t in m.get("hashtags") or [])


def _add_hit(pool: dict[str, dict], m: dict, term: str) -> bool:
    """Count one discovery hit for the row's author; False when the row names none."""
    un = (m.get("author") or "").lower()
    if not un:
        return False
    rec = pool.setdefault(un, {"hits": 0, "terms": set(), "captions": []})
    rec["hits"] += 1
    rec["terms"].add(term)
    captext = _caption_text(m)
    if captext:
        rec["captions"].append(captext[:200])
    return True


def _walk(method: str, body: dict, key: str, pages: int, label: str) -> list[dict]:
    """Read up to `pages` cursor pages; a refused page ends this walk only (fatal errors propagate)."""
    rows: list[dict] = []
    cursor: str | None = None
    for page in range(pages):
        page_body = {**body, "limit": PAGE_SIZE}
        if cursor:
            page_body["cursor"] = cursor
        try:
            d = _loore.call(method, page_body, key=key)
        except _loore.LooreError as e:
            if e.fatal:
                raise
            log.warning("%s p%d failed: %s", label, page, e)
            break
        items = d.get("items") or []
        rows += items
        log.info("%s p%d: +%d", label, page, len(items))
        cursor = d.get("nextCursor")
        if not d.get("hasMore") or not cursor or not items:
            break
    return rows


# ---------- Phase 1: discovery ----------

def discover(key: str, pages: int) -> dict[str, dict]:
    """Return {username: {hits:int, terms:set, captions:[...]}}."""
    pool: dict[str, dict] = {}
    for kw in KEYWORDS:
        seen_ids: set[str] = set()
        for m in _walk("ig-search", {"kind": "reels", "query": kw}, key, pages, f"kw='{kw}'"):
            mid = str(m.get("code") or m.get("id") or "")
            if mid in seen_ids:
                continue
            seen_ids.add(mid)
            _add_hit(pool, m, kw)
        log.info("kw='%s': pool=%d", kw, len(pool))

    # hashtag harvest -- different surface, catches prolific taggers
    for tag in HASHTAGS:
        body = {"hashtag": tag, "rank": "reels", "include_caption": True}
        for m in _walk("ig-hashtag-media", body, key, 2, f"tag=#{tag}"):
            _add_hit(pool, m, "#" + tag)
        log.info("tag=#%s: pool=%d", tag, len(pool))
    return pool


# ---------- Phase 2: enrich profile ----------

def _profile(username: str, key: str) -> dict | None:
    """One ig_profile read mapped to the creator row; None when unavailable."""
    try:
        d = _loore.call("ig-profile", {"username": username}, key=key)
    except _loore.LooreError as e:
        if e.fatal and not e.private_account:
            raise
        log.debug("profile @%s failed: %s", username, e)
        return None
    u = d.get("profile") or {}
    if not u.get("id"):
        return None
    return {
        "username": u.get("username") or username,
        "pk": str(u.get("id")),
        "full_name": u.get("fullName") or "",
        "biography": u.get("biography") or "",
        "follower_count": int(u.get("followers") or 0),
        "media_count": int(u.get("posts") or 0),
        "is_private": bool(u.get("isPrivate")),
        "is_verified": bool(u.get("isVerified")),
        "category": u.get("category") or "",
    }


# ---------- Phase 3: cadence ----------

def _clips_cadence(pk: str, key: str) -> dict:
    """Posting cadence from one ig_user_reels page (pinned reels left out)."""
    empty = {"reels_per_month": 0.0, "n_clips": 0, "days_since_last": 9999, "captions": []}
    try:
        d = _loore.call("ig-user-reels", {"user_id": pk, "limit": CADENCE_PAGE, "include_caption": True}, key=key)
    except _loore.LooreError as e:
        if e.fatal and not e.private_account:
            raise
        log.debug("clips %s failed: %s", pk, e)
        return empty
    ts: list[float] = []
    caps: list[str] = []
    for m in d.get("items") or []:
        # A pinned reel heads the feed whatever its age and would stretch the span.
        if m.get("isPinned"):
            continue
        t = iso_to_epoch(m.get("takenAt"))
        if t:
            ts.append(t)
        captext = _caption_text(m)
        if captext:
            caps.append(captext[:200])
    if not ts:
        return {**empty, "captions": caps}
    ts.sort(reverse=True)
    now = time.time()
    newest, oldest = ts[0], ts[-1]
    span_days = (newest - oldest) / 86400.0
    n = len(ts)
    rate = (n / span_days) * 30.0 if span_days > 0.5 else float(n)
    return {
        "reels_per_month": round(rate, 1),
        "n_clips": n,
        "days_since_last": round((now - newest) / 86400.0, 1),
        "captions": caps,
    }


def _cyrillic_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    cyr = sum(1 for c in letters if "Ѐ" <= c <= "ӿ")
    return cyr / len(letters)


def _topic_hits(text: str) -> int:
    t = text.lower()
    return sum(1 for term in TOPIC_TERMS if term in t)


async def run(args: argparse.Namespace) -> int:
    key = _loore.api_key()
    state = args.out_dir / "state"
    state.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_event_loop()
    sem = asyncio.Semaphore(args.parallel)

    # caches (username-keyed) -- make re-runs incremental & cheap
    cache_dir = args.out_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    prof_cache_path = cache_dir / "profiles.json"
    cad_cache_path = cache_dir / "cadence.json"
    prof_cache: dict[str, dict] = json.loads(prof_cache_path.read_text()) if prof_cache_path.exists() else {}
    cad_cache: dict[str, dict] = json.loads(cad_cache_path.read_text()) if cad_cache_path.exists() else {}
    log.info("cache loaded: %d profiles, %d cadence", len(prof_cache), len(cad_cache))

    # --- Phase 1 ---
    log.info("=== Phase 1: discovery (%d keywords x %d pages) ===", len(KEYWORDS), args.pages)
    pool = await loop.run_in_executor(None, discover, key, args.pages)
    # Optional seed list of accounts you already know are in the niche.
    # Ships empty: copy data/watchlist.example.json -> data/watchlist.json and
    # fill it with YOUR accounts, or point $WATCHLIST at any JSON of the same shape.
    wl_path = Path(os.environ.get("WATCHLIST") or Path(__file__).resolve().parent.parent / "data" / "watchlist.json")
    seed = []
    if wl_path.exists():
        try:
            wl = json.loads(wl_path.read_text())
            seed = [a["username"].lower() for a in wl.get("accounts", []) if a.get("username")]
        except (ValueError, TypeError, KeyError, AttributeError):
            log.warning("watchlist %s is unreadable, continuing without seed", wl_path)
    for un in seed:
        pool.setdefault(un, {"hits": 0, "terms": set(), "captions": []})
    for un in pool:
        pool[un]["terms"] = sorted(pool[un]["terms"])
    (state / "pool.json").write_text(json.dumps(pool, ensure_ascii=False, indent=2))
    log.info("discovery pool: %d unique candidates (+%d watchlist seed)", len(pool), len(seed))

    # --- Phase 2 ---
    log.info("=== Phase 2: enrich profiles (followers gate >=%d) ===", args.min_followers)
    usernames = list(pool.keys())

    async def enrich(un: str) -> dict | None:
        if un in prof_cache:
            return dict(prof_cache[un])
        async with sem:
            p = await loop.run_in_executor(None, _profile, un, key)
        if p:
            prof_cache[un] = dict(p)
        return p

    to_fetch = [u for u in usernames if u not in prof_cache]
    log.info("  profiles: %d cached, %d to fetch", len(usernames) - len(to_fetch), len(to_fetch))
    profiles: list[dict] = []
    done = 0
    for coro in asyncio.as_completed([enrich(u) for u in usernames]):
        p = await coro
        done += 1
        if done % 50 == 0:
            log.info("  enriched %d/%d", done, len(usernames))
        if not p:
            continue
        p["discovery_hits"] = pool.get(p["username"].lower(), {}).get("hits", 0)
        profiles.append(p)
    prof_cache_path.write_text(json.dumps(prof_cache, ensure_ascii=False))
    qualified = [p for p in profiles if p["follower_count"] >= args.min_followers and not p["is_private"]]
    (state / "profiles.json").write_text(json.dumps(profiles, ensure_ascii=False, indent=2))
    log.info("profiles ok: %d | passed followers+public gate: %d", len(profiles), len(qualified))

    # --- Phase 3 ---
    log.info("=== Phase 3: cadence + topic + english (%d accounts) ===", len(qualified))

    async def cad(p: dict) -> dict:
        un = p["username"].lower()
        if un in cad_cache:
            c = cad_cache[un]
        else:
            async with sem:
                c = await loop.run_in_executor(None, _clips_cadence, p["pk"], key)
            cad_cache[un] = c
        text = " ".join([p["full_name"], p["biography"]] + c["captions"] + pool.get(un, {}).get("captions", []))
        p["reels_per_month"] = c["reels_per_month"]
        p["n_clips"] = c["n_clips"]
        p["days_since_last"] = c["days_since_last"]
        p["topic_hits"] = _topic_hits(text)
        p["cyrillic_ratio"] = round(_cyrillic_ratio(p["biography"] + " " + p["full_name"]), 2)
        return p

    n_cad_new = sum(1 for p in qualified if p["username"].lower() not in cad_cache)
    log.info("  cadence: %d cached, %d to fetch", len(qualified) - n_cad_new, n_cad_new)
    enriched: list[dict] = []
    done = 0
    for coro in asyncio.as_completed([cad(p) for p in qualified]):
        enriched.append(await coro)
        done += 1
        if done % 50 == 0:
            log.info("  cadence %d/%d", done, len(qualified))
    cad_cache_path.write_text(json.dumps(cad_cache, ensure_ascii=False))

    # gates
    def is_english(p: dict) -> bool:
        return p["cyrillic_ratio"] <= 0.15

    strict = [
        p for p in enriched
        if p["reels_per_month"] >= args.min_reels_month
        and p["topic_hits"] >= 1
        and is_english(p)
        and p["days_since_last"] <= 21
    ]
    strict.sort(key=lambda p: (p["reels_per_month"], p["follower_count"]), reverse=True)

    # ranked fallback pool (English + topic + active), best cadence first, to reach target
    ranked = [
        p for p in enriched
        if p["topic_hits"] >= 1 and is_english(p) and p["days_since_last"] <= 45
    ]
    ranked.sort(key=lambda p: (p["reels_per_month"], p["follower_count"]), reverse=True)
    top = ranked[: args.target]

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "criteria": {
            "min_followers": args.min_followers,
            "min_reels_month": args.min_reels_month,
            "english_only": True,
            "active_within_days": 21,
        },
        "counts": {
            "discovery_pool": len(pool),
            "profiles_ok": len(profiles),
            "followers_public_gate": len(qualified),
            "strict_pass": len(strict),
            "ranked_top": len(top),
        },
        "strict_pass": strict,
        "ranked_top100": top,
    }
    (args.out_dir / "creators.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    # readable
    lines = [
        f"CREATORS HUNT -- {out['generated_at']}",
        f"criteria: >={args.min_followers} followers, >={args.min_reels_month} reels/mo, English, active<=21d",
        f"pool={len(pool)} profiles_ok={len(profiles)} followers_gate={len(qualified)} STRICT={len(strict)}",
        "",
        f"=== STRICT PASS ({len(strict)}) -- meet ALL criteria ===",
    ]
    for i, p in enumerate(strict, 1):
        lines.append(f"{i:3d}. @{p['username']:<24} {p['follower_count']:>9,} foll | {p['reels_per_month']:>5.0f} reels/mo | last {p['days_since_last']:.0f}d | {p['full_name'][:30]}")
    lines += ["", f"=== RANKED TOP {len(top)} (by cadence, English+topic+active<=45d) ==="]
    for i, p in enumerate(top, 1):
        flag = "*" if p in strict else " "
        lines.append(f"{i:3d}.{flag}@{p['username']:<24} {p['follower_count']:>9,} foll | {p['reels_per_month']:>5.0f} reels/mo | last {p['days_since_last']:.0f}d")
    (args.out_dir / "creators.txt").write_text("\n".join(lines))

    log.info("DONE. strict=%d top=%d -> %s", len(strict), len(top), args.out_dir / "creators.json")
    print(f"\nSTRICT_PASS={len(strict)} RANKED_TOP={len(top)}")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)
    args = parse_args()
    try:
        return asyncio.run(run(args))
    except _loore.LooreError as e:
        log.error("%s", e.hint())
        return 1


if __name__ == "__main__":
    sys.exit(main())
