#!/usr/bin/env python3
"""Filter reels by AI/agent-related keywords."""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("reel-radar.3")


def load_keywords() -> list[re.Pattern]:
    raw = (SKILL_ROOT / "config" / "keywords.txt").read_text().splitlines()
    kws = [k.strip().lower() for k in raw if k.strip() and not k.startswith("#")]
    patterns = []
    for kw in kws:
        esc = re.escape(kw)
        patterns.append(re.compile(rf"(?:^|[^\wа-яё]){esc}(?:[^\wа-яё]|$)", re.IGNORECASE))
    return patterns


def is_relevant(reel: dict, patterns: list[re.Pattern]) -> tuple[bool, list[str]]:
    haystack = " ".join(
        str(reel.get(f, "") or "") for f in ("caption", "author_bio", "author")
    ).lower()
    matched = [p.pattern for p in patterns if p.search(haystack)]
    return bool(matched), matched


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) < 2:
        log.error("usage: 3-filter-relevant.py <output_dir>")
        return 2
    out_dir = Path(sys.argv[1])

    reels = json.loads((out_dir / "state" / "reels-raw.json").read_text())
    patterns = load_keywords()
    log.info("loaded %d keyword patterns", len(patterns))

    relevant = []
    for r in reels:
        ok, matched = is_relevant(r, patterns)
        if ok:
            r["matched_keywords"] = matched[:10]
            relevant.append(r)

    target = out_dir / "state" / "reels-relevant.json"
    target.write_text(json.dumps(relevant, ensure_ascii=False, indent=2))
    log.info("wrote %s (%d/%d relevant)", target, len(relevant), len(reels))
    return 0


if __name__ == "__main__":
    sys.exit(main())
