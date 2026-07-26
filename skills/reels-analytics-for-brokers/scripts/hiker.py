"""Tiny HikerAPI client: rate limiting, retries, defensive response parsing.

No third-party dependencies — stdlib only, so the scripts run on any machine
with Python 3.9+.

Auth: export HIKER_API_KEY (or HIKER_KEY). Get a key at https://hikerapi.com.
Never hardcode the key and never print it.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterator

log = logging.getLogger("hiker")

# api.instagrapi.com is the same service without the Cloudflare bot-check that
# tends to reject plain urllib/requests calls made from scripts.
BASE_URL = os.environ.get("HIKER_BASE_URL", "https://api.instagrapi.com")

# HikerAPI bills per request. Keep this in one place so cost estimates in the
# scripts stay honest; check your own tier via GET /sys/balance.
def _price_from_env(default: float = 0.001) -> float:
    """Read the per-request price, falling back rather than dying at import."""
    try:
        return float(os.environ.get("HIKER_PRICE_PER_REQUEST", default))
    except (TypeError, ValueError):
        log.warning("HIKER_PRICE_PER_REQUEST is not a number, using %s", default)
        return default


PRICE_PER_REQUEST_USD = _price_from_env()


class HikerError(RuntimeError):
    """Raised when the API keeps failing after all retries."""


class RateLimiter:
    """Thread-safe minimum-interval limiter.

    HikerAPI allows a handful of requests per second depending on tier. Staying
    below the cap is what keeps a long run from being throttled, so every call
    goes through here.
    """

    def __init__(self, rps: float) -> None:
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


class Hiker:
    """Counting, rate-limited HikerAPI client."""

    def __init__(self, key: str | None = None, rps: float = 6.0, timeout: int = 30) -> None:
        self.access_key = key or os.environ.get("HIKER_API_KEY") or os.environ.get("HIKER_KEY") or ""
        if not self.access_key:
            raise HikerError(
                "HIKER_API_KEY is not set. Get a key at https://hikerapi.com and "
                "export HIKER_API_KEY=... (do not hardcode it)."
            )
        self.limiter = RateLimiter(rps)
        self.timeout = timeout
        self.requests_used = 0
        # Workers share one client, and this counter is reported to the user as
        # the run's cost — `+=` is a read-modify-write and can lose increments.
        self._counter_lock = threading.Lock()

    @property
    def spent_usd(self) -> float:
        """Approximate spend of this run, in USD."""
        return self.requests_used * PRICE_PER_REQUEST_USD

    def get(self, path: str, params: dict[str, Any] | None = None, retries: int = 4) -> dict[str, Any]:
        """GET a HikerAPI endpoint with retry + exponential backoff.

        Args:
            path: Endpoint path, e.g. ``/v2/user/by/username``.
            params: Query parameters.
            retries: How many times to retry on 429/5xx/network errors.

        Returns:
            Parsed JSON body (``{}`` on a 404, which is a normal "not found").

        Raises:
            HikerError: When every attempt failed.
        """
        query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v not in (None, "")})
        url = f"{BASE_URL}{path}?{query}" if query else f"{BASE_URL}{path}"
        last_err: Exception | None = None

        for attempt in range(retries + 1):
            self.limiter.wait()
            request = urllib.request.Request(url, headers={"accept": "application/json", "x-access-key": self.access_key})
            try:
                with self._counter_lock:
                    self.requests_used += 1
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8", errors="replace"))
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    return {}
                last_err = err
                # 429/5xx are transient; 4xx other than 404 are not worth retrying.
                if err.code not in (429, 500, 502, 503, 504):
                    raise HikerError(f"{path} -> HTTP {err.code}") from err
            except Exception as err:  # network hiccups, timeouts, bad JSON
                last_err = err
            if attempt < retries:
                backoff = 2.0**attempt
                log.warning("%s failed (%s), retry in %.0fs", path, last_err, backoff)
                time.sleep(backoff)

        raise HikerError(f"{path} failed after {retries + 1} attempts: {last_err}")


def unwrap(payload: dict[str, Any], *keys: str) -> Any:
    """Pull the first present key out of a payload or its ``response`` envelope.

    HikerAPI shapes differ between v1/v2/gql endpoints — some return the object
    directly, some wrap it in ``response``. Rather than hardcoding one shape and
    breaking on the next endpoint, look in both places.
    """
    for source in (payload, payload.get("response") if isinstance(payload.get("response"), dict) else {}):
        if not isinstance(source, dict):
            continue
        for key in keys:
            if source.get(key) is not None:
                return source[key]
    return None


def paginate(client: Hiker, path: str, params: dict[str, Any], item_keys: tuple[str, ...],
             max_pages: int = 20, page_param: str = "page_id",
             empty_page_budget: int = 1) -> Iterator[list[dict[str, Any]]]:
    """Yield pages of items until the cursor runs out or ``max_pages`` is hit.

    The cursor field is inconsistent across endpoints (``next_page_id``,
    ``next_max_id``, ``end_cursor``), so all of them are checked.

    Two failure modes are handled explicitly because both cost money silently:
    a server that keeps handing back the SAME cursor would otherwise be paid for
    ``max_pages`` identical fetches, and a single empty page in the middle of a
    walk would otherwise abandon everything after it.
    """
    cursor: str | None = None
    seen_cursors: set[str] = set()
    empty_pages = 0

    for _ in range(max_pages):
        page_params = dict(params)
        if cursor:
            page_params[page_param] = cursor
        payload = client.get(path, page_params)
        items = unwrap(payload, *item_keys) or []
        if not isinstance(items, list):
            items = []
        yield items

        if not items:
            empty_pages += 1
            if empty_pages > empty_page_budget:
                return
        else:
            empty_pages = 0

        cursor = unwrap(payload, "next_page_id", "next_max_id", "end_cursor")
        # `not cursor` would also swallow a legitimate numeric 0 cursor.
        if cursor is None or cursor == "":
            return
        cursor = str(cursor)
        if cursor in seen_cursors:
            log.debug("%s returned a repeating cursor, stopping pagination", path)
            return
        seen_cursors.add(cursor)


def num(value: Any, cast: Any, default: Any = 0) -> Any:
    """Cast an API field that is *usually* numeric but sometimes arrives as text.

    The API occasionally returns ``"12 345"`` or an ISO timestamp where a number
    is documented. Raising there would surface three layers up as a generic
    "error" and look exactly like an empty niche, so coerce what we can and fall
    back to the default instead of exploding.
    """
    if value is None:
        return default
    try:
        return cast(value)
    except (TypeError, ValueError):
        pass
    try:
        cleaned = str(value).replace("\u00a0", "").replace(" ", "").replace(",", "")
        return cast(cleaned)
    except (TypeError, ValueError):
        return default


def media_fields(media: dict[str, Any]) -> dict[str, Any]:
    """Normalise a media object into the flat shape every script downstream uses.

    Caption lives under ``caption.text`` on some endpoints and ``caption_text``
    on others; views are ``play_count`` or ``view_count``.
    """
    caption = media.get("caption")
    caption_text = caption.get("text", "") if isinstance(caption, dict) else (media.get("caption_text") or "")
    code = media.get("code") or ""
    return {
        "code": code,
        "pk": str(media.get("pk") or media.get("id") or ""),
        "caption": caption_text,
        "views": num(media.get("play_count") or media.get("view_count"), int, 0),
        "likes": num(media.get("like_count"), int, 0),
        "comments": num(media.get("comment_count"), int, 0),
        "duration": num(media.get("video_duration"), float, 0.0),
        "taken_at": num(media.get("taken_at") or media.get("taken_at_ts"), float, 0.0),
        "url": f"https://www.instagram.com/reel/{code}/" if code else "",
    }
