#!/usr/bin/env python3
"""Transcript of a YouTube video or Short through Loore yt_transcript (public captions).

Usage:
    python3 yt_transcript.py <youtube_url|id> [--timestamps] [--json] [--lang ru] [--original] [--no-meta]

Text (default): "# <title> — <channel>" header, a blank line, then the transcript;
with --timestamps every line is "[hh:mm:ss] text".
--json: {"video_id", "language", "transcript", "metadata": {"title", "author_name"}} where
"transcript" is a string, or a list of {"text", "start", "duration"} with --timestamps.

Cost: yt_transcript 2 credits when a transcript is returned (no captions = free; continuing a
long transcript with offset is free), the yt_video header lookup 1.5 credits (skip: --no-meta).
The official YouTube Data API cannot download captions of other people's videos, so there is
no API alternative here. Exit codes: 1 Loore refused, 2 bad input, 3 no key, 4 no captions /
Loore rate window longer than the client waits.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _loore  # noqa: E402

log = logging.getLogger("yt-transcript")

VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})")
# Upper bound on continuation calls for one transcript (40000 chars / 400 segments each).
MAX_WINDOWS = 50


def video_id(s: str) -> str:
    """The 11-char video id of any YouTube link form, or the bare id itself."""
    m = VIDEO_ID_RE.search(s)
    if m:
        return m.group(1)
    s = s.strip()
    return s if re.fullmatch(r"[A-Za-z0-9_-]{11}", s) else ""


def _pick(d: dict[str, Any], *keys: str) -> Any:
    """First non-empty value among `keys` (Loore documents fields by meaning, not by schema)."""
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return None


def _hms(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def fetch(vid: str, timestamps: bool, language: str | None, original: bool) -> tuple[str | None, Any]:
    """All windows of one transcript: (language, text or list of segments)."""
    body: dict[str, Any] = {"url": vid, "include_timestamps": timestamps}
    if language:
        body["language"] = language
    if original:
        body["original_audio"] = True
    text_parts: list[str] = []
    segments: list[dict[str, Any]] = []
    lang: str | None = None
    for _ in range(MAX_WINDOWS):
        result = _loore.call("yt-transcript", body)
        lang = lang or _pick(result, "language", "lang")
        if timestamps:
            for seg in result.get("segments") or []:
                if not isinstance(seg, dict):
                    continue
                start = float(_pick(seg, "start") or 0)
                end = _pick(seg, "end")
                dur = float(_pick(seg, "duration") or (float(end) - start if end is not None else 0))
                segments.append({"text": str(_pick(seg, "text") or ""), "start": start, "duration": round(dur, 3)})
        else:
            text_parts.append(str(_pick(result, "text", "transcript") or ""))
        nxt = result.get("nextOffset")
        if not result.get("truncated") or nxt is None:
            break
        body["offset"] = int(nxt)
    if timestamps:
        return lang, segments
    return lang, "".join(text_parts)


def metadata(vid: str) -> tuple[dict[str, Any], list[Any]]:
    """Title and channel from yt_video, plus the caption languages it lists."""
    result = _loore.call("yt-video", {"url": vid})
    v = result.get("video") if isinstance(result.get("video"), dict) else result
    ch = v.get("channel")
    author = (_pick(ch, "name", "title", "handle") if isinstance(ch, dict)
              else _pick(v, "channel", "channelName", "channelTitle", "author"))
    langs = v.get("captionLanguages")
    return {"title": v.get("title") or "", "author_name": author or ""}, langs if isinstance(langs, list) else []


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="YouTube transcript via Loore yt_transcript.")
    ap.add_argument("video", help="YouTube link (watch, youtu.be, shorts, live) or 11-char id")
    ap.add_argument("--timestamps", action="store_true", help="timed segments: [hh:mm:ss] text")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    ap.add_argument("--lang", help="caption language, e.g. ru, en or en-US")
    ap.add_argument("--original", action="store_true", help="only captions in the original spoken language")
    ap.add_argument("--no-meta", action="store_true", help="skip the yt_video title lookup (saves 1.5 credits)")
    args = ap.parse_args()

    vid = video_id(args.video)
    if not vid:
        log.error("не удалось извлечь id видео из: %s", args.video)
        return 2
    _loore.api_key()
    try:
        meta, langs = ({"title": "", "author_name": ""}, []) if args.no_meta else metadata(vid)
        lang, transcript = fetch(vid, args.timestamps, args.lang, args.original)
    except _loore.LooreError as e:
        if e.http_status == 404:
            log.error("видео не найдено или у него нет субтитров (%s)", e.error)
            return 4
        log.error("%s", e.hint())
        return 1
    if not transcript:
        extra = f" – доступные языки: {', '.join(map(str, langs))}" if langs else ""
        log.error("у видео нет публичных субтитров на этом языке%s", extra)
        return 4

    if args.json:
        print(json.dumps({"video_id": vid, "language": lang, "transcript": transcript, "metadata": meta},
                         ensure_ascii=False, indent=2))
        return 0
    if meta["title"] or meta["author_name"]:
        print(f"# {meta['title']} — {meta['author_name']}\n")
    if args.timestamps:
        print("\n".join(f"[{_hms(s['start'])}] {s['text']}" for s in transcript))
    else:
        print(transcript)
    return 0


if __name__ == "__main__":
    sys.exit(main())
