#!/usr/bin/env python3
"""yt-research — YouTube niche/competitor search + stats.

Default path: Loore (https://docs.loore.ai, needs LOORE_API_KEY): yt_search, yt_channel_videos,
yt_channel_shorts, yt_trending_shorts, yt_video, yt_channel, yt_comments.
Optional: the official YouTube Data API v3 (--api, needs YOUTUBE_API_KEY) for search, channel
videos and comments. The API key travels in the X-goog-api-key header, never in a URL or argv.

Ranks results by views and by view-velocity (views/day since upload) to spot what's taking off.
YouTube data is never scraped from this machine (no yt-dlp / innertube / oEmbed).
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import math
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _loore  # noqa: E402

log = logging.getLogger("yt-research")

# Loore's YouTube answers are documented by field meaning, not by a JSON schema, so rows are
# read by the first key present. Unknown shapes are logged by key name (never by value).
LIST_KEYS = ("items", "results", "videos", "shorts", "comments", "rows")
# A Loore list page; more pages than this per search/channel is never fetched (each costs credits).
MAX_PAGES = 5
YT_API = "https://www.googleapis.com/youtube/v3"
VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})")
CHANNEL_ID_RE = re.compile(r"^UC[A-Za-z0-9_-]{20,24}$")


# ---------- shared helpers ----------

def _pick(d: dict[str, Any], *keys: str) -> Any:
    """First non-empty value among `keys` (Loore field names are read tolerantly)."""
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return None


def _num(v: Any) -> int | None:
    """Int from a number or a numeric string like "12,345"; None when absent."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = re.sub(r"[,\s_]", "", str(v))
    return int(float(s)) if re.fullmatch(r"\d+(\.\d+)?", s) else None


def _seconds(v: Any) -> int | None:
    """Duration in seconds from a number, "h:mm:ss"/"mm:ss" or ISO-8601 "PT1H2M3S"."""
    n = _num(v)
    if n is not None:
        return n
    if not isinstance(v, str):
        return None
    if re.fullmatch(r"\d+(:\d{1,2}){1,2}", v):
        total = 0
        for part in v.split(":"):
            total = total * 60 + int(part)
        return total
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", v)
    if m and any(m.groups()):
        d, h, mi, s = (int(x or 0) for x in m.groups())
        return ((d * 24 + h) * 60 + mi) * 60 + s
    return None


_REL_UNITS = {"second": 1 / 86400, "minute": 1 / 1440, "hour": 1 / 24, "day": 1, "week": 7,
              "month": 30, "year": 365}


def _upload_date(v: Any) -> str | None:
    """YYYYMMDD from ISO-8601, YYYY-MM-DD, YYYYMMDD or YouTube's relative "3 weeks ago"."""
    if not v:
        return None
    s = str(v).strip()
    if re.fullmatch(r"\d{8}", s):
        return s
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "".join(m.groups())
    m = re.search(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", s)
    if m:
        days = int(m.group(1)) * _REL_UNITS[m.group(2)]
        return (datetime.date.today() - datetime.timedelta(days=math.floor(days))).strftime("%Y%m%d")
    return None


def _name(v: Any) -> str | None:
    """Channel/author name from a string or an object with name/title/handle."""
    if isinstance(v, dict):
        return _pick(v, "name", "title", "handle", "username")
    return str(v) if v else None


def video_id(s: str) -> str:
    """The 11-char video id of any YouTube link form, or the bare id itself."""
    m = VIDEO_ID_RE.search(s)
    if m:
        return m.group(1)
    return s if re.fullmatch(r"[A-Za-z0-9_-]{11}", s) else ""


def _rows(result: dict[str, Any], method: str) -> list[dict[str, Any]]:
    for k in LIST_KEYS:
        v = result.get(k)
        if isinstance(v, list):
            return [x for x in v if isinstance(x, dict)]
    log.warning("%s: no row list in the answer (keys: %s)", method, ", ".join(sorted(result)) or "-")
    return []


def _object(result: dict[str, Any], key: str) -> dict[str, Any]:
    """`result[key]` when the answer nests the object (like ig-profile's `profile`), else result."""
    v = result.get(key)
    return v if isinstance(v, dict) else result


def norm_row(d: dict[str, Any]) -> dict[str, Any]:
    """One Loore video/Short row in the shape this script prints."""
    vid = _pick(d, "id", "videoId") or video_id(str(d.get("url") or ""))
    return {
        "id": vid,
        "kind": _pick(d, "kind", "type"),
        "title": _pick(d, "title"),
        "channel": _name(_pick(d, "channel", "channelName", "channelTitle", "author")),
        "views": _num(_pick(d, "views", "viewCount")),
        "likes": _num(_pick(d, "likes", "likeCount")),
        "comments": _num(_pick(d, "comments", "commentCount")),
        "duration": _seconds(_pick(d, "durationSec", "duration", "lengthSeconds")),
        "upload_date": _upload_date(_pick(d, "publishedAt", "publishDate", "published", "uploadDate",
                                          "publishedText", "takenAt")),
        "url": _pick(d, "url") or (f"https://youtu.be/{vid}" if vid else None),
    }


# ---------- Loore (default) ----------

def loore_list(method: str, body: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    """Walk nextCursor pages of a Loore YouTube listing until `limit` rows or MAX_PAGES."""
    out: list[dict[str, Any]] = []
    cursor: str | None = None
    for _ in range(MAX_PAGES):
        page = dict(body)
        if cursor:
            page["cursor"] = cursor
        result = _loore.call(method, page)
        out += [norm_row(r) for r in _rows(result, method)]
        if result.get("filterNote"):
            log.info("%s: %s", method, result["filterNote"])
        cursor = result.get("nextCursor")
        if len(out) >= limit or not cursor or result.get("hasMore") is False:
            break
    return out[:limit]


def _channel_subject(handle: str) -> dict[str, str]:
    h = handle.strip()
    if CHANNEL_ID_RE.match(h):
        return {"channel_id": h}
    return {"handle": "@" + h.lstrip("@")}


def loore_search(args: argparse.Namespace) -> list[dict[str, Any]]:
    body: dict[str, Any] = {"query": args.query, "type": args.type}
    for flag, key in (("upload_date", "upload_date"), ("sort", "sort_by"), ("region", "region"),
                      ("length", "duration")):
        if getattr(args, flag):
            body[key] = getattr(args, flag)
    return loore_list("yt-search", body, args.limit)


def loore_channel(handle: str, limit: int, shorts: bool) -> list[dict[str, Any]]:
    method, sort = ("yt-channel-shorts", "newest") if shorts else ("yt-channel-videos", "latest")
    rows = loore_list(method, {**_channel_subject(handle), "sort": sort}, limit)
    for r in rows:
        r["channel"] = r["channel"] or handle.lstrip("@")
    return rows


def loore_enrich(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fill upload_date / likes / comments / channel_subs with yt_video (+ yt_channel once per channel)."""
    subs_cache: dict[str, int | None] = {}
    for r in rows:
        if not r.get("url"):
            continue
        try:
            v = _object(_loore.call("yt-video", {"url": r["url"]}), "video")
        except _loore.LooreError as e:
            if e.fatal:
                raise
            log.warning("yt-video %s: %s", r["id"], e)
            continue
        full = norm_row(v)
        # yt_video's date is exact; a search row's date is approximate («3 weeks ago»).
        r["upload_date"] = full.get("upload_date") or r.get("upload_date")
        for k in ("likes", "comments", "views", "duration", "title"):
            r[k] = r.get(k) or full.get(k)
        ch = v.get("channel")
        ch_ref = (_pick(ch, "id", "channelId", "handle", "url") if isinstance(ch, dict)
                  else _pick(v, "channelId", "channelHandle", "channelUrl"))
        if not ch_ref:
            continue
        if ch_ref not in subs_cache:
            subject = ({"url": ch_ref} if str(ch_ref).startswith("http")
                       else _channel_subject(str(ch_ref)))
            try:
                c = _object(_loore.call("yt-channel", subject), "channel")
                subs_cache[ch_ref] = _num(_pick(c, "subscribers", "subscriberCount"))
            except _loore.LooreError as e:
                if e.fatal:
                    raise
                subs_cache[ch_ref] = None
        r["channel_subs"] = subs_cache[ch_ref]
    return rows


def loore_comments(url: str, order: str, limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cursor: str | None = None
    for _ in range(MAX_PAGES):
        body: dict[str, Any] = {"url": url, "order": order}
        if cursor:
            body["cursor"] = cursor
        result = _loore.call("yt-comments", body)
        for c in _rows(result, "yt-comments"):
            out.append({
                "author": _name(_pick(c, "author", "authorName")),
                "text": _pick(c, "text", "content"),
                "likes": _num(_pick(c, "likes", "likeCount")),
                "replies": _num(_pick(c, "replyCount", "replies")),
                "date": _pick(c, "publishedAt", "date", "published", "publishedText"),
                "replies_token": c.get("repliesToken"),
            })
        cursor = result.get("nextCursor")
        if len(out) >= limit or not cursor:
            break
    return out[:limit]


# ---------- Optional: YouTube Data API v3 (needs YOUTUBE_API_KEY) ----------

def _api_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        sys.exit("YOUTUBE_API_KEY не задан – уберите --api (основной путь – Loore) "
                 "или создайте ключ (см. SKILL.md, раздел YouTube Data API v3).")
    req = urllib.request.Request(f"{YT_API}/{path}?{urllib.parse.urlencode(params)}",
                                 headers={"X-goog-api-key": key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode("utf-8", "replace")).get("error", {}).get("message", "")
        except (json.JSONDecodeError, AttributeError):
            msg = ""
        sys.exit(f"YouTube Data API {e.code} on {path}: {msg or e.reason}")


def _api_videos(ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i in range(0, len(ids), 50):
        vids = _api_get("videos", {"part": "snippet,statistics,contentDetails",
                                   "id": ",".join(ids[i:i + 50])}).get("items", [])
        for v in vids:
            st, sn = v.get("statistics", {}), v.get("snippet", {})
            rows.append({
                "id": v["id"], "title": sn.get("title"), "channel": sn.get("channelTitle"),
                "views": _num(st.get("viewCount")), "likes": _num(st.get("likeCount")),
                "comments": _num(st.get("commentCount")),
                "duration": _seconds(v.get("contentDetails", {}).get("duration")),
                "upload_date": _upload_date(sn.get("publishedAt")), "url": f"https://youtu.be/{v['id']}",
            })
    return rows


def api_search(query: str, limit: int) -> list[dict[str, Any]]:
    """search.list (100 quota units) + videos.list (1 unit)."""
    items = _api_get("search", {"part": "snippet", "q": query, "type": "video",
                                "maxResults": min(limit, 50), "order": "viewCount"}).get("items", [])
    return _api_videos([it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")])


def api_channel(handle: str, limit: int) -> list[dict[str, Any]]:
    """channels.list → uploads playlist → playlistItems.list → videos.list (a few units)."""
    h = handle.strip()
    params = {"part": "contentDetails,statistics"}
    params.update({"id": h} if CHANNEL_ID_RE.match(h) else {"forHandle": "@" + h.lstrip("@")})
    chans = _api_get("channels", params).get("items", [])
    if not chans:
        log.warning("channel %s not found", handle)
        return []
    uploads = chans[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    subs = _num(chans[0].get("statistics", {}).get("subscriberCount"))
    items = _api_get("playlistItems", {"part": "contentDetails", "playlistId": uploads,
                                       "maxResults": min(limit, 50)}).get("items", [])
    rows = _api_videos([it["contentDetails"]["videoId"] for it in items])
    for r in rows:
        r["channel_subs"] = subs
    return rows


def api_comments(url: str, order: str, limit: int) -> list[dict[str, Any]]:
    """commentThreads.list (1 unit)."""
    vid = video_id(url)
    if not vid:
        sys.exit(f"не удалось извлечь id видео из: {url}")
    items = _api_get("commentThreads", {"part": "snippet", "videoId": vid, "maxResults": min(limit, 100),
                                        "order": "time" if order == "newest" else "relevance",
                                        "textFormat": "plainText"}).get("items", [])
    out = []
    for it in items:
        sn = it.get("snippet", {})
        top = sn.get("topLevelComment", {}).get("snippet", {})
        out.append({"author": top.get("authorDisplayName"), "text": top.get("textDisplay"),
                    "likes": _num(top.get("likeCount")), "replies": _num(sn.get("totalReplyCount")),
                    "date": top.get("publishedAt"), "replies_token": None})
    return out


# ---------- ranking + output ----------

def velocity(r: dict[str, Any]) -> int | None:
    ud, v = r.get("upload_date"), r.get("views")
    if not ud or not v:
        return None
    try:
        d = datetime.datetime.strptime(str(ud), "%Y%m%d").date()
    except ValueError:
        return None
    days = max((datetime.date.today() - d).days, 1)
    return round(v / days)


def fmt(rows: list[dict[str, Any]], by: str) -> list[dict[str, Any]]:
    rows = [r for r in rows if r.get("views")]
    for r in rows:
        r["velocity"] = velocity(r)
    keyfn = (lambda r: r.get("velocity") or 0) if by == "velocity" else (lambda r: r.get("views") or 0)
    rows.sort(key=keyfn, reverse=True)
    return rows


def print_comments(rows: list[dict[str, Any]], as_json: bool) -> None:
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    for i, c in enumerate(rows, 1):
        text = " ".join(str(c.get("text") or "").split())[:300]
        print(f"{i:>2}. {c.get('likes') or 0:>6,} likes | {c.get('replies') or 0:>3} replies — {c.get('author') or '?'}: {text}")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="YouTube niche/competitor research (Loore or YouTube Data API v3).")
    ap.add_argument("query", nargs="?", default="", help="search query (RU/EN)")
    ap.add_argument("--handles", help="comma-separated channel handles (or UC… ids) to scan instead of search")
    ap.add_argument("--shorts", action="store_true", help="with --handles: the channels' Shorts (Loore only)")
    ap.add_argument("--trending-shorts", action="store_true", help="Shorts trending on YouTube now (Loore only)")
    ap.add_argument("--comments", metavar="URL", help="comments under a video instead of search")
    ap.add_argument("--order", choices=["top", "newest"], default="top", help="comment order (default top)")
    ap.add_argument("--limit", type=int, default=15, help="results per search/channel (default 15)")
    ap.add_argument("--by", choices=["views", "velocity"], default="views", help="ranking key")
    ap.add_argument("--enrich", action="store_true", help="add upload_date/likes/comments/subs per video")
    ap.add_argument("--type", choices=["videos", "shorts"], default="videos", help="search: videos or shorts")
    ap.add_argument("--upload-date", choices=["today", "this_week", "this_month", "this_year"],
                    help="search: only content uploaded in this window (Loore)")
    ap.add_argument("--sort", choices=["relevance", "popular"], help="search order (Loore, default relevance)")
    ap.add_argument("--length", choices=["under_3_min", "between_3_and_20_min", "over_20_min"],
                    help="search: duration filter (Loore)")
    ap.add_argument("--region", help="search: two-letter country code, e.g. US or RU (Loore)")
    ap.add_argument("--api", action="store_true", help="use YouTube Data API v3 (needs YOUTUBE_API_KEY)")
    ap.add_argument("--json", action="store_true", help="print raw JSON")
    args = ap.parse_args()
    if args.api and (args.shorts or args.trending_shorts):
        ap.error("--shorts and --trending-shorts exist only on the Loore path (drop --api)")

    try:
        if args.comments:
            rows = (api_comments if args.api else loore_comments)(args.comments, args.order, args.limit)
            print_comments(rows, args.json)
            return 0
        rows = []
        if args.trending_shorts:
            rows = loore_list("yt-trending-shorts", {}, args.limit)
        elif args.handles:
            for h in [x.strip() for x in args.handles.split(",") if x.strip()]:
                rows += api_channel(h, args.limit) if args.api else loore_channel(h, args.limit, args.shorts)
        elif args.query:
            rows = api_search(args.query, args.limit) if args.api else loore_search(args)
        else:
            ap.error("provide a query, --handles, --trending-shorts or --comments")

        # The official path already carries dates and stats; Loore rows may lack them.
        needs = args.enrich or (args.by == "velocity" and any(not r.get("upload_date") for r in rows))
        if needs and not args.api:
            rows = loore_enrich(rows)
    except _loore.LooreError as e:
        log.error("%s", e.hint())
        return 1
    rows = fmt(rows, args.by)

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    for i, r in enumerate(rows, 1):
        vel = f" | {r['velocity']:,}/day" if r.get("velocity") else ""
        dur = f" | {int(r['duration'] // 60)}m" if r.get("duration") else ""
        print(f"{i:>2}. {r['views']:>9,} views{vel}{dur} — {r['title']}")
        print(f"    {r.get('channel') or '?'} — {r['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
