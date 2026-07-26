#!/usr/bin/env python3
"""Composite ranking: rank_views + rank_comments + rank_er. Lower = better."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

log = logging.getLogger("reel-radar.4")


def rank_map(values: list[float]) -> dict[int, int]:
    indexed = sorted(enumerate(values), key=lambda x: x[1], reverse=True)
    return {idx: rank for rank, (idx, _) in enumerate(indexed, 1)}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    reels = json.loads((args.output_dir / "state" / "reels-relevant.json").read_text())
    if not reels:
        log.error("no relevant reels to rank")
        return 4

    views = [float(r.get("play_count", 0)) for r in reels]
    comments = [float(r.get("comment_count", 0)) for r in reels]
    ers = []
    for r in reels:
        followers = max(int(r.get("author_followers", 0) or 0), 1)
        interactions = int(r.get("like_count", 0)) + int(r.get("comment_count", 0))
        ers.append(interactions / followers)

    rv = rank_map(views)
    rc = rank_map(comments)
    re_rank = rank_map(ers)

    for idx, r in enumerate(reels):
        r["rank_views"] = rv[idx]
        r["rank_comments"] = rc[idx]
        r["rank_er"] = re_rank[idx]
        r["engagement_rate"] = round(ers[idx] * 100, 3)
        r["composite"] = rv[idx] + rc[idx] + re_rank[idx]

    reels.sort(key=lambda r: r["composite"])
    top = reels[: args.top]

    target = args.output_dir / "state" / "reels-top25.json"
    target.write_text(json.dumps(top, ensure_ascii=False, indent=2))
    log.info("wrote %s (top %d of %d)", target, len(top), len(reels))
    return 0


if __name__ == "__main__":
    sys.exit(main())
