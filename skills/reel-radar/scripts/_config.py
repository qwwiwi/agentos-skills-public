#!/usr/bin/env python3
"""Shared config resolution for reel-radar scripts.

Priority: CLI argument > env var > config/defaults.json.
No account, key or chat id is hardcoded anywhere in this skill.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

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
    """Read the data-provider key from the environment (HIKER_KEY or HIKER_API_KEY)."""
    key = (os.environ.get("HIKER_KEY") or os.environ.get("HIKER_API_KEY") or "").strip()
    if not key:
        print("HIKER_KEY env var is empty — export your key from https://hikerapi.com", file=sys.stderr)
        raise SystemExit(3)
    return key
