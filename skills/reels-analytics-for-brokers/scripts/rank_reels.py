#!/usr/bin/env python3
"""Step 4: rank reels by SPIKE against the account's own median — not by raw views.

Absolute views rank accounts, not ideas. A 40k-view reel from a 200k-follower
agency is its Tuesday; the same 40k from a 500-follower broker means the
algorithm pushed that video to strangers, and the only thing that could have
caused it is the content itself. Ranking by spike surfaces the second case,
which is the one you can copy.

Three numbers per reel, and they answer different questions:
  spike        views / account median  — did THIS video outperform its author?
  reach_ratio  views / followers       — did it leave the author's audience at all?
  er           (likes + comments) / views — how warm was the traffic?

Engagement is deliberately measured against views, not followers. Measured per
follower it goes UP on a breakout and tells you nothing; per view it goes DOWN,
which is the honest signal that a hit is cold reach rather than a warm audience.

Usage:
  python3 rank_reels.py --out runs/2026-07-26 --top 250 --days 14

Reads:  <out>/accounts.json, <out>/reels.json
Writes: <out>/top-reels.json, <out>/top-reels.csv, <out>/summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("rank")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank reels by spike over the account's own median.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--config", type=Path,
                        help="niche config; supplies defaults for --days (ranking_days) and --top (top_reels)")
    parser.add_argument("--top", type=int, help="how many reels to keep (default 250, or top_reels from --config)")
    parser.add_argument("--days", type=int,
                        help="ranking window, shorter than the qualification window "
                             "(default 14, or ranking_days from --config)")
    parser.add_argument("--min-views", type=int, default=300,
                        help="floor that stops a 30-view account from producing fake 10x spikes")
    parser.add_argument("--min-account-reels", type=int, default=5,
                        help="an account needs this many reels for its median to mean anything")
    args = parser.parse_args()

    # The config is the place a reader edits first when porting the skill to a
    # new niche, so the window and depth keys there have to actually do
    # something. Explicit flags still win over the config.
    config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
    if args.days is None:
        args.days = int(config.get("ranking_days", 14))
    if args.top is None:
        args.top = int(config.get("top_reels", 250))
    if args.top < 1:
        parser.error("--top must be >= 1")
    if args.days < 1:
        parser.error("--days must be >= 1")
    return args


def percentile(values: list[float], fraction: float) -> float:
    """Rounded-index percentile; avoids a numpy dependency.

    Not the nearest-rank definition — for n=10 the 0.9 fraction lands on the
    9th value rather than the 10th. Close enough for a sanity figure in the
    summary, but do not quote it as a formal percentile.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(fraction * (len(ordered) - 1)))))
    return ordered[index]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()

    accounts = {a["username"]: a for a in json.loads((args.out / "accounts.json").read_text(encoding="utf-8"))}
    reels = json.loads((args.out / "reels.json").read_text(encoding="utf-8"))
    cutoff_ts = (datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp()

    scored: list[dict[str, Any]] = []
    for reel in reels:
        account = accounts.get(reel.get("account", ""))
        if not account or reel["taken_at"] < cutoff_ts:
            continue
        if account["reels_in_window"] < args.min_account_reels:
            continue
        views = reel["views"]
        if views < args.min_views:
            continue

        # A zero median cannot produce a meaningful spike. Substituting 1.0 would
        # silently turn a 5,000-view reel into a "5000x breakout" and hand it the
        # leader slot — skip the account instead of inventing a denominator.
        median_views = float(account["median_views"])
        if median_views <= 0:
            continue
        followers = max(int(account["followers"]), 1)
        interactions = reel["likes"] + reel["comments"]

        scored.append({
            **reel,
            "followers": followers,
            "account_median_views": median_views,
            "spike": round(views / median_views, 2),
            "reach_ratio": round(views / followers, 2),
            "reach_pct": round(100.0 * views / followers, 1),
            "er_pct": round(100.0 * interactions / views, 2) if views else 0.0,
            "posted": datetime.fromtimestamp(reel["taken_at"], tz=timezone.utc).date().isoformat(),
        })

    if not scored:
        log.error("nothing to rank — widen --days, lower --min-views, or check that qualification produced reels")
        return 3

    scored.sort(key=lambda r: r["spike"], reverse=True)
    top = scored[: args.top]

    (args.out / "top-reels.json").write_text(json.dumps(top, ensure_ascii=False, indent=2), encoding="utf-8")

    columns = ["posted", "account", "followers", "views", "spike", "reach_pct", "er_pct",
               "likes", "comments", "duration", "url", "caption"]
    with (args.out / "top-reels.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for reel in top:
            writer.writerow({**reel, "caption": (reel.get("caption") or "").replace("\n", " ")[:300]})

    all_views = [r["views"] for r in scored]
    all_er = [r["er_pct"] for r in scored]
    leader = top[0]
    summary = {
        "window_days": args.days,
        "accounts_in_sample": len({r["account"] for r in scored}),
        "reels_in_sample": len(scored),
        "median_views": round(statistics.median(all_views), 1),
        "p90_views": round(percentile([float(v) for v in all_views], 0.9), 1),
        "median_er_pct": round(statistics.median(all_er), 2),
        "breakouts_over_3x": sum(1 for r in scored if r["spike"] >= 3),
        "leader": {
            "account": leader["account"], "followers": leader["followers"], "views": leader["views"],
            "spike": leader["spike"], "reach_pct": leader["reach_pct"], "er_pct": leader["er_pct"],
            "url": leader["url"],
        },
    }
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("ranked %d reels from %d accounts | sample median %.0f views | %d breakouts >=3x",
             len(scored), summary["accounts_in_sample"], summary["median_views"], summary["breakouts_over_3x"])
    log.info("leader: @%s %d followers -> %d views (spike %.1fx, reach %.0f%%, ER %.2f%%)",
             leader["account"], leader["followers"], leader["views"],
             leader["spike"], leader["reach_pct"], leader["er_pct"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
