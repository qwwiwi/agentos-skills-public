#!/usr/bin/env python3
"""Score top-25 candidates against prince's own top-10 reels, pick top-15.

Relevance heuristic (0-100):
  - Theme overlap (keyword Jaccard) × 40
  - Formula match (STOP doing / guide / hack / провокация) × 30
  - Engagement profile similarity (views band) × 30

Usage: python3 8-relevance-match.py <output_dir> [--top 15]
Reads: <output_dir>/state/reels-top25.json, <output_dir>/state/own-reels.json,
       <output_dir>/transcripts/*.txt
Writes: <output_dir>/state/reels-top15.json
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

log = logging.getLogger("reel-radar.8")

FORMULAS = [
    ("stop_doing", re.compile(r"\b(stop|хватит|перестан|не надо)\b", re.I)),
    ("you_didnt_know", re.compile(r"\b(ты не знал|did ?n.?t know|не знал(а|и)?|shocking|удивит)\b", re.I)),
    ("step_guide", re.compile(r"\b(пошаго|step[- ]?by[- ]?step|гайд|how to|как сделать)\b", re.I)),
    ("hack", re.compile(r"\b(хак|секрет|лайфхак|hack|trick|трюк)\b", re.I)),
    ("provocation", re.compile(r"\b(все врут|никто|забудь|forget|nobody)\b", re.I)),
    ("comparison", re.compile(r"\b(vs|против|лучше чем|better than)\b", re.I)),
    ("warning", re.compile(r"\b(warning|осторожно|не делай|don.?t)\b", re.I)),
]


def text_tokens(text: str) -> set[str]:
    return set(re.findall(r"[а-яёa-z0-9]{4,}", text.lower()))


def detect_formula(text: str) -> str:
    for name, pat in FORMULAS:
        if pat.search(text):
            return name
    return "other"


def engagement_band(views: int) -> str:
    if views > 500_000:
        return "viral"
    if views > 100_000:
        return "hit"
    if views > 20_000:
        return "mid"
    return "low"


def score(candidate_text: str, candidate_views: int, own: list[dict]) -> tuple[float, dict]:
    c_tokens = text_tokens(candidate_text)
    c_formula = detect_formula(candidate_text)
    c_band = engagement_band(candidate_views)

    theme_best = 0.0
    formula_hit = 0
    band_hit = 0
    best_ref_code = ""

    for o in own:
        o_text = o.get("caption", "") or ""
        o_tokens = text_tokens(o_text)
        if c_tokens and o_tokens:
            inter = len(c_tokens & o_tokens)
            union = len(c_tokens | o_tokens)
            jaccard = inter / union if union else 0
        else:
            jaccard = 0
        if jaccard > theme_best:
            theme_best = jaccard
            best_ref_code = o.get("code", "")
        if detect_formula(o_text) == c_formula and c_formula != "other":
            formula_hit = 1
        if engagement_band(int(o.get("play_count", 0))) == c_band:
            band_hit = 1

    total = round(theme_best * 40 + formula_hit * 30 + band_hit * 30, 1)
    return total, {
        "formula": c_formula,
        "theme_jaccard": round(theme_best, 3),
        "formula_match": bool(formula_hit),
        "band_match": bool(band_hit),
        "engagement_band": c_band,
        "best_ref_code": best_ref_code,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    candidates = json.loads((args.output_dir / "state" / "reels-top25.json").read_text())
    own = json.loads((args.output_dir / "state" / "own-reels.json").read_text())
    tx_dir = args.output_dir / "transcripts"

    for i, c in enumerate(candidates, 1):
        tx_file = tx_dir / f"{i}.txt"
        transcript = tx_file.read_text().strip() if tx_file.exists() else ""
        blob = " ".join([c.get("caption", ""), transcript])
        s, meta = score(blob, int(c.get("play_count", 0)), own)
        c["relevance_score"] = s
        c["relevance_meta"] = meta
        c["transcript"] = transcript

    candidates.sort(key=lambda r: r["relevance_score"], reverse=True)
    top = candidates[: args.top]

    target = args.output_dir / "state" / "reels-top15.json"
    target.write_text(json.dumps(top, ensure_ascii=False, indent=2))
    log.info("wrote %s (top %d by relevance)", target, len(top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
