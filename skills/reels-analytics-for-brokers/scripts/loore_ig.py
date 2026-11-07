#!/usr/bin/env python3
"""Instagram helpers for this skill on top of the Loore client (loore.py).

What lives here and not in loore.py:
  - a shared, thread-safe client that rate-limits calls and counts both the
    calls made and the credits Loore reports in every answer
    (``creditsChargedMilli``) — that sum is the honest cost of a run;
  - cursor pagination that survives a repeating cursor and one empty page;
  - ``media_fields()``: one Loore media row -> the flat reel shape every
    downstream script (rank_reels.py, offers_diff.py) reads;
  - a tiny CLI used by teardown_reel.sh, so the shell script never touches
    the API key.

Auth: export LOORE_API_KEY (app.loore.ai → Настройки → API и MCP,
docs: https://docs.loore.ai). The key is read from the environment only and
never printed. Paid calls carry $LOORE_SPEND_AUTHORIZATION_ID automatically.

CLI (teardown_reel.sh):
  python3 loore_ig.py media <CODE> <META_OUT>          ig-media -> meta.json
  python3 loore_ig.py download <CODE> <VIDEO_OUT>      ig-download -> video file
  python3 loore_ig.py comments <MEDIA_ID> <JSON_OUT>   ig-media-comments, first page
  python3 loore_ig.py transcribe <CODE> <TEXT_OUT>     video-transcribe -> plain text

Exit codes: 0 ok, 2 refused call (a Russian hint goes to stderr),
3 no LOORE_API_KEY, 4 the media is gone, private or not a video.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from loore import LooreError, api_key, call

log = logging.getLogger("loore-ig")

DOWNLOAD_TIMEOUT = 180


class RateLimiter:
    """Thread-safe minimum-interval limiter.

    Loore budgets requests per key per minute and per day (the size depends on
    the plan). Spreading calls evenly keeps a long run from burning the
    minute's budget in a burst and then waiting on 429s.
    """

    def __init__(self, rps: float) -> None:
        """Create a limiter.

        Args:
            rps: Maximum calls per second; 0 or less disables the limit.
        """
        self._min_interval = 1.0 / rps if rps > 0 else 0.0
        self._lock = threading.Lock()
        self._next_at = 0.0

    def wait(self) -> None:
        """Block until the next request is allowed."""
        with self._lock:
            now = time.monotonic()
            if now < self._next_at:
                time.sleep(self._next_at - now)
                now = time.monotonic()
            self._next_at = now + self._min_interval


class Client:
    """Counting, rate-limited wrapper over ``loore.call``."""

    def __init__(self, rps: float = 2.0) -> None:
        """Read the key (exits with a Russian hint when it is missing).

        Args:
            rps: Calls-per-second cap shared by every worker thread.
        """
        self.key = api_key()
        self.limiter = RateLimiter(rps)
        self.requests_used = 0
        self._credits_milli = 0
        # Workers share one client and these counters are reported to the user
        # as the run's cost — `+=` is a read-modify-write and can lose updates.
        self._counter_lock = threading.Lock()

    @property
    def credits_charged(self) -> float:
        """Credits Loore reported as charged for this run so far."""
        return self._credits_milli / 1000.0

    def call(self, method: str, body: dict[str, Any]) -> dict[str, Any]:
        """Call one Loore method and count it.

        Args:
            method: REST method name, e.g. ``ig-profile``.
            body: JSON arguments exactly as in the contract.

        Returns:
            The envelope's ``result``; ``{}`` on a 404, which is a normal
            "not found" for a renamed or deleted account.

        Raises:
            LooreError: Any other refusal (``.fatal`` says retrying is pointless).
        """
        self.limiter.wait()
        with self._counter_lock:
            self.requests_used += 1
        try:
            result = call(method, body, key=self.key)
        except LooreError as err:
            if err.http_status == 404:
                return {}
            raise
        charged = num(result.get("creditsChargedMilli"), int, 0)
        with self._counter_lock:
            self._credits_milli += charged
        return result


def paginate(client: Client, method: str, body: dict[str, Any], max_pages: int = 10,
             empty_page_budget: int = 1) -> Iterator[list[dict[str, Any]]]:
    """Yield pages of ``items`` until ``hasMore`` is false or ``max_pages`` is hit.

    Two failure modes are handled explicitly because both cost money silently:
    a server that keeps handing back the SAME cursor would otherwise be paid for
    ``max_pages`` identical fetches, and a single empty page in the middle of a
    walk would otherwise abandon everything after it.

    A walk that starts by handle continues by the ``accountId`` the first answer
    published — the contract allows it and it skips a handle lookup per page.

    Args:
        client: Shared client.
        method: Paginated Loore method (items / hasMore / nextCursor).
        body: First-page arguments.
        max_pages: Hard ceiling on paid pages.
        empty_page_budget: Empty pages tolerated in a row before stopping.

    Yields:
        The ``items`` list of each page (possibly empty).
    """
    page_body = dict(body)
    seen_cursors: set[str] = set()
    empty_pages = 0

    for _ in range(max_pages):
        result = client.call(method, page_body)
        items = result.get("items")
        items = [row for row in items if isinstance(row, dict)] if isinstance(items, list) else []
        yield items

        if not items:
            empty_pages += 1
            if empty_pages > empty_page_budget:
                return
        else:
            empty_pages = 0

        cursor = result.get("nextCursor")
        if not result.get("hasMore") or not isinstance(cursor, str) or not cursor:
            return
        if cursor in seen_cursors:
            log.debug("%s returned a repeating cursor, stopping pagination", method)
            return
        seen_cursors.add(cursor)
        page_body["cursor"] = cursor
        account_id = result.get("accountId")
        if "username" in page_body and isinstance(account_id, str) and account_id.isdigit():
            page_body.pop("username")
            page_body["user_id"] = account_id


def num(value: Any, cast: Callable[[Any], Any], default: Any = 0) -> Any:
    """Cast a field that is *usually* numeric but may be missing or text.

    Loore omits a count it did not receive instead of zero-filling it, so a
    missing field must fall back to the default rather than raise three layers
    up and look exactly like an empty niche.

    Args:
        value: Raw field value.
        cast: ``int`` or ``float``.
        default: Returned when the value cannot be cast.

    Returns:
        The cast value or ``default``.
    """
    if value is None:
        return default
    try:
        return cast(value)
    except (TypeError, ValueError):
        pass
    try:
        cleaned = str(value).replace(" ", "").replace(" ", "").replace(",", "")
        return cast(cleaned)
    except (TypeError, ValueError):
        return default


def parse_ts(value: Any) -> float:
    """ISO-8601 ``takenAt`` -> unix seconds (0.0 when absent or unparsable).

    Args:
        value: The row's ``takenAt``.

    Returns:
        Unix timestamp in seconds.
    """
    if not isinstance(value, str) or not value:
        return 0.0
    # Python < 3.11 accepts only 3 or 6 fractional digits; seconds are enough.
    cleaned = re.sub(r"\.\d+", "", value.strip()).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def media_fields(media: dict[str, Any]) -> dict[str, Any]:
    """Normalise a Loore media row into the flat shape every script downstream uses.

    Field mapping: ``id`` -> pk, ``takenAt`` (ISO) -> taken_at (unix seconds),
    ``durationSec`` -> duration. ``views`` is absent when Loore received no
    positive play count; it becomes 0 and is dropped from medians downstream.
    ``likes`` is absent when the author hid it (``likesHidden``); ``likes_hidden``
    keeps that mark so ER is not computed from a fake zero.

    Args:
        media: One row of ig-user-reels / ig-hashtag-media, or ig-media's ``media``.

    Returns:
        Flat reel record.
    """
    code = str(media.get("code") or "")
    return {
        "code": code,
        "pk": str(media.get("id") or ""),
        "caption": str(media.get("caption") or ""),
        "views": num(media.get("views"), int, 0),
        "likes": num(media.get("likes"), int, 0),
        "likes_hidden": bool(media.get("likesHidden")),
        "comments": num(media.get("comments"), int, 0),
        "duration": num(media.get("durationSec"), float, 0.0),
        "taken_at": parse_ts(media.get("takenAt")),
        "url": f"https://www.instagram.com/reel/{code}/" if code else str(media.get("url") or ""),
        # Loore marks rows that must not shape the author's median: a pinned
        # old hit heading the feed and a trial reel shown to non-followers only.
        "is_pinned": bool(media.get("isPinned")),
        "is_trial": bool(media.get("isTrial")),
    }


def reel_url(code: str) -> str:
    """Public permalink for a shortcode."""
    return f"https://www.instagram.com/reel/{code}/"


def _write_json(path: Path, data: Any) -> None:
    """Write UTF-8 JSON, keeping Cyrillic readable."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_media(client: Client, code: str, out: Path) -> int:
    """ig-media -> meta.json in the shape the old teardown produced (+ kind, author).

    Returns:
        0 for a video, 4 when the reel is gone, private or not a video.
    """
    result = client.call("ig-media", {"media_url_or_code": code})
    media = result.get("media")
    if not isinstance(media, dict):
        _write_json(out, {"code": code, "video_url_found": False, "note": str(result.get("note") or "not found")})
        return 4
    meta = media_fields(media)
    meta.pop("is_pinned", None)
    meta.pop("is_trial", None)
    meta["kind"] = str(media.get("kind") or "unknown")
    meta["author"] = str(media.get("author") or "")
    meta["video_url_found"] = meta["kind"] == "video"
    _write_json(out, meta)
    return 0 if meta["video_url_found"] else 4


def cmd_download(client: Client, code: str, out: Path) -> int:
    """ig-download -> the video file.

    Prefers the key-free signed ``downloadUrl`` (lives ~15 minutes, so it is
    fetched immediately and never written to disk); falls back to the artifact
    link, which needs the key as a Bearer header.

    Returns:
        0 on success, 4 when nothing was delivered.
    """
    result = client.call("ig-download", {"url": reel_url(code)})
    artifact = result.get("artifact") if isinstance(result.get("artifact"), dict) else {}
    signed = result.get("downloadUrl")
    if isinstance(signed, str) and signed.startswith("https://"):
        request = urllib.request.Request(signed)
    elif isinstance(artifact.get("url"), str) and artifact["url"].startswith("https://"):
        request = urllib.request.Request(artifact["url"], headers={"Authorization": f"Bearer {client.key}"})
    else:
        log.error("ig-download returned no file link")
        return 4
    tmp = out.with_suffix(out.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response, tmp.open("wb") as handle:
            while chunk := response.read(1 << 16):
                handle.write(chunk)
        tmp.replace(out)
    finally:
        tmp.unlink(missing_ok=True)
    return 0


def cmd_comments(client: Client, media_id: str, out: Path) -> int:
    """ig-media-comments, first page of up to 50 top-level comments -> JSON file."""
    result = client.call("ig-media-comments", {"media_id": media_id, "limit": 50})
    _write_json(out, {"mediaId": media_id, "items": result.get("items") or [],
                      "hasMore": bool(result.get("hasMore")), "note": result.get("note")})
    return 0


def cmd_transcribe(client: Client, code: str, out: Path) -> int:
    """video-transcribe -> plain transcript text (the format offers_diff.py reads)."""
    # include_words stays at its default: with it off Loore caps `text` at 4000
    # characters, and the transcript is read whole by offers_diff.py.
    result = client.call("video-transcribe", {"url": reel_url(code)})
    text = result.get("text")
    if not isinstance(text, str) or not text.strip():
        return 4
    out.write_text(text.strip() + "\n", encoding="utf-8")
    return 0


def main() -> int:
    """CLI entry point for teardown_reel.sh."""
    parser = argparse.ArgumentParser(description="Loore Instagram helpers used by teardown_reel.sh.")
    parser.add_argument("command", choices=["media", "download", "comments", "transcribe"])
    parser.add_argument("subject", help="reel shortcode (media/download/transcribe) or numeric media id (comments)")
    parser.add_argument("out", type=Path, help="output file")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.command == "comments" and not args.subject.isdigit():
        log.error("media id must be numeric")
        return 2
    handlers = {"media": cmd_media, "download": cmd_download, "comments": cmd_comments,
                "transcribe": cmd_transcribe}
    client = Client(rps=0)
    try:
        return handlers[args.command](client, args.subject, args.out)
    except LooreError as err:
        print(err.hint(), file=sys.stderr)
        return 2
    except (urllib.error.URLError, OSError) as err:
        # A failed file fetch: the signed link went stale or the network dropped.
        log.error("%s failed: %s", args.command, err)
        return 2


if __name__ == "__main__":
    sys.exit(main())
