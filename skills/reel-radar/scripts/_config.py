#!/usr/bin/env python3
"""Shared config resolution for reel-radar scripts.

Priority: CLI argument > env var > config/defaults.json.
No account, key or chat id is hardcoded anywhere in this skill.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import _loore

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = SKILL_ROOT / "config" / "defaults.json"


def load_config() -> dict:
    """Read config/defaults.json (empty dict if the file is missing or broken)."""
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def target_user(cli_value: str | None = None) -> str:
    """Resolve the reference Instagram account whose following list is scanned.

    Args:
        cli_value: value passed on the command line, if any.

    Returns:
        Instagram username without the leading @.

    Exits with code 3 when nothing is configured — an empty username would
    otherwise produce a confusing 404 from the data provider.
    """
    value = (cli_value or os.environ.get("TARGET_USER") or load_config().get("target_user") or "").strip()
    value = value.lstrip("@")
    if not value:
        print(
            "target account is not set. Use --username, or export TARGET_USER=<instagram_login>, "
            f'or fill "target_user" in {CONFIG_FILE}',
            file=sys.stderr,
        )
        raise SystemExit(3)
    return value


def api_key() -> str:
    """Read the Loore key from $LOORE_API_KEY (exits 3 with a hint when empty)."""
    return _loore.api_key()


def iso_to_epoch(value: str | None) -> float:
    """Convert Loore's ISO-8601 takenAt to a unix timestamp (0.0 when absent)."""
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def reel_row(item: dict) -> dict:
    """Map one Loore media row (ig_user_reels / ig_search) to the reel shape the pipeline uses.

    Loore omits a count it did not receive instead of zero-filling it; the
    pipeline's numeric fields keep their 0 fallback. Hidden likes are not zero:
    `likes_hidden` marks them so ER is not computed for that reel.
    """
    code = item.get("code", "")
    return {
        "code": code,
        "pk": str(item.get("id", "")),
        "caption": item.get("caption") or " ".join(f"#{t}" for t in item.get("hashtags") or []),
        "play_count": int(item.get("views") or 0),
        "like_count": int(item.get("likes") or 0),
        "likes_hidden": bool(item.get("likesHidden")),
        "comment_count": int(item.get("comments") or 0),
        "video_duration": float(item.get("durationSec") or 0),
        "taken_at": iso_to_epoch(item.get("takenAt")),
        "url": item.get("url") or (f"https://www.instagram.com/reel/{code}/" if code else ""),
    }
