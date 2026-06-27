#!/usr/bin/env python3
"""yt-research — YouTube niche/competitor search + stats.

Default path: yt-dlp (no API key). Optional: YouTube Data API v3 (--api, needs YOUTUBE_API_KEY).
Ranks results by views and by view-velocity (views/day since upload) to spot what's taking off.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request


def _run(cmd, timeout=150):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _parse_jsonl(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append({
            "id": d.get("id"),
            "title": d.get("title"),
            "channel": d.get("channel") or d.get("uploader"),
            "views": d.get("view_count"),
            "duration": d.get("duration"),
            "url": d.get("url") or (f"https://youtu.be/{d.get('id')}" if d.get("id") else None),
        })
    return rows


def ytdlp_search(query, limit):
    cmd = ["yt-dlp", f"ytsearch{limit}:{query}", "--flat-playlist", "--dump-json", "--no-warnings"]
    return _parse_jsonl(_run(cmd).stdout)


def ytdlp_channel(handle, limit):
    h = handle.lstrip("@")
    url = f"https://www.youtube.com/@{h}/videos"
    cmd = ["yt-dlp", url, "--flat-playlist", "--dump-json", "--playlist-end", str(limit), "--no-warnings"]
    rows = _parse_jsonl(_run(cmd).stdout)
    for r in rows:
        r["channel"] = r["channel"] or h
    return rows


def enrich(rows):
    """Add upload_date / likes / comments / channel_subs via full per-video extract."""
    for r in rows:
        if not r.get("url"):
            continue
        cmd = ["yt-dlp", r["url"], "--dump-single-json", "--skip-download", "--no-warnings"]
        try:
            d = json.loads(_run(cmd, 90).stdout)
        except (json.JSONDecodeError, subprocess.TimeoutExpired):
            continue
        r["upload_date"] = d.get("upload_date")
        r["likes"] = d.get("like_count")
        r["comments"] = d.get("comment_count")
        r["channel_subs"] = d.get("channel_follower_count")
        if not r.get("views"):
            r["views"] = d.get("view_count")
    return rows


def velocity(r):
    ud, v = r.get("upload_date"), r.get("views")
    if not ud or not v:
        return None
    try:
        d = datetime.datetime.strptime(str(ud), "%Y%m%d").date()
        days = max((datetime.date.today() - d).days, 1)
        return round(v / days)
    except ValueError:
        return None


# ---- Optional: YouTube Data API v3 (needs YOUTUBE_API_KEY) ----
def api_search(query, limit):
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        sys.exit("YOUTUBE_API_KEY not set — use the default yt-dlp path (drop --api), "
                 "or provision a key (see SKILL.md › Setup).")
    base = "https://www.googleapis.com/youtube/v3"
    q = urllib.parse.urlencode({"part": "snippet", "q": query, "type": "video",
                                "maxResults": min(limit, 50), "order": "viewCount", "key": key})
    with urllib.request.urlopen(f"{base}/search?{q}", timeout=30) as resp:
        items = json.load(resp).get("items", [])
    ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
    if not ids:
        return []
    q2 = urllib.parse.urlencode({"part": "snippet,statistics", "id": ",".join(ids), "key": key})
    with urllib.request.urlopen(f"{base}/videos?{q2}", timeout=30) as resp:
        vids = json.load(resp).get("items", [])
    rows = []
    for v in vids:
        st, sn = v.get("statistics", {}), v.get("snippet", {})
        pub = sn.get("publishedAt", "")[:10].replace("-", "")
        rows.append({
            "id": v["id"], "title": sn.get("title"), "channel": sn.get("channelTitle"),
            "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)) if st.get("likeCount") else None,
            "comments": int(st.get("commentCount", 0)) if st.get("commentCount") else None,
            "upload_date": pub, "url": f"https://youtu.be/{v['id']}",
        })
    return rows


def fmt(rows, by):
    rows = [r for r in rows if r.get("views")]
    for r in rows:
        r["velocity"] = velocity(r)
    keyfn = (lambda r: r.get("velocity") or 0) if by == "velocity" else (lambda r: r.get("views") or 0)
    rows.sort(key=keyfn, reverse=True)
    return rows


def main():
    ap = argparse.ArgumentParser(description="YouTube niche/competitor research (yt-dlp or Data API).")
    ap.add_argument("query", nargs="?", default="", help="search query (RU/EN)")
    ap.add_argument("--handles", help="comma-separated channel handles to scan instead of search")
    ap.add_argument("--limit", type=int, default=15, help="results per search/channel (default 15)")
    ap.add_argument("--by", choices=["views", "velocity"], default="views", help="ranking key")
    ap.add_argument("--enrich", action="store_true", help="fetch upload_date/likes (needed for --by velocity)")
    ap.add_argument("--api", action="store_true", help="use YouTube Data API v3 (needs YOUTUBE_API_KEY)")
    ap.add_argument("--json", action="store_true", help="print raw JSON")
    args = ap.parse_args()

    rows = []
    if args.handles:
        for h in [x.strip() for x in args.handles.split(",") if x.strip()]:
            rows += ytdlp_channel(h, args.limit)
    elif args.api:
        rows = api_search(args.query, args.limit)
    elif args.query:
        rows = ytdlp_search(args.query, args.limit)
    else:
        ap.error("provide a query or --handles")

    if (args.enrich or args.by == "velocity") and not args.api:
        rows = enrich(rows)
    rows = fmt(rows, args.by)

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    for i, r in enumerate(rows, 1):
        vel = f" | {r['velocity']:,}/day" if r.get("velocity") else ""
        dur = f" | {int(r['duration'] // 60)}m" if r.get("duration") else ""
        print(f"{i:>2}. {r['views']:>9,} views{vel}{dur} — {r['title']}")
        print(f"    {r.get('channel', '?')} — {r['url']}")


if __name__ == "__main__":
    main()
