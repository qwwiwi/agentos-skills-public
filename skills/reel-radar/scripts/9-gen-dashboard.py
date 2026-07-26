#!/usr/bin/env python3
"""Generate dashboard.html from 25 candidates + statistics summary.

Usage: python3 9-gen-dashboard.py <output_dir>
Reads: <output_dir>/state/reels-top25.json, <output_dir>/state/following.json,
       <output_dir>/state/reels-relevant.json, <skill_root>/templates/dashboard.html
Writes: <output_dir>/dashboard.html
"""
from __future__ import annotations

import html
import json
import logging
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("reel-radar.9")

FORMULA_LABELS = {
    "stop_doing": "STOP doing X",
    "you_didnt_know": "Ты не знал",
    "step_guide": "Пошаговый гайд",
    "hack": "Лайфхак",
    "provocation": "Провокация",
    "comparison": "Сравнение",
    "warning": "Предостережение",
    "other": "Другое",
}


def fmt_num(n: float | int) -> str:
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n/1_000:.1f}K".replace(".0K", "K")
    return str(n)


def detect_theme(text: str) -> str:
    t = text.lower()
    if "claude" in t or "клод" in t:
        return "Claude"
    if "cursor" in t:
        return "Cursor"
    if "gpt" in t or "chatgpt" in t or "openai" in t:
        return "GPT"
    if "agent" in t or "агент" in t:
        return "AI-агенты"
    if "mcp" in t:
        return "MCP"
    if "n8n" in t or "zapier" in t or "make.com" in t or "automation" in t:
        return "Автоматизация"
    if "no-code" in t or "no code" in t or "нокод" in t:
        return "No-code"
    return "AI"


def detect_formula_from_meta(reel: dict) -> str:
    meta = reel.get("relevance_meta") or {}
    f = meta.get("formula")
    if f:
        return f
    cap = (reel.get("caption") or "").lower()
    if "stop" in cap or "хватит" in cap:
        return "stop_doing"
    if "гайд" in cap or "how to" in cap:
        return "step_guide"
    return "other"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) < 2:
        log.error("usage: 9-gen-dashboard.py <output_dir>")
        return 2
    out_dir = Path(sys.argv[1])

    reels = json.loads((out_dir / "state" / "reels-top25.json").read_text())
    following = json.loads((out_dir / "state" / "following.json").read_text())
    relevant = json.loads((out_dir / "state" / "reels-relevant.json").read_text())

    tpl = (SKILL_ROOT / "templates" / "dashboard.html").read_text()

    views = [int(r.get("play_count", 0)) for r in reels]
    ers = [float(r.get("engagement_rate", 0)) for r in reels]
    authors = Counter(r.get("author", "") for r in reels)
    formulas = Counter(detect_formula_from_meta(r) for r in reels)

    rows = []
    for i, r in enumerate(reels, 1):
        theme = detect_theme(r.get("caption", ""))
        formula = FORMULA_LABELS.get(detect_formula_from_meta(r), "—")
        caption = html.escape((r.get("caption") or "")[:200])
        rows.append(
            "<tr>"
            f'<td><span class="rank">{i:02d}</span></td>'
            f'<td><div class="author">@{html.escape(r.get("author",""))}</div>'
            f'<div class="caption">{caption}…</div>'
            f'<div class="meta-row"><span class="pill">{html.escape(theme)}</span></div></td>'
            f'<td class="num">{fmt_num(r.get("play_count",0))}</td>'
            f'<td class="num">{fmt_num(r.get("comment_count",0))}</td>'
            f'<td class="num">{r.get("engagement_rate",0)}</td>'
            f'<td>{html.escape(formula)}</td>'
            f'<td><a href="{html.escape(r.get("url",""))}" target="_blank">open</a></td>'
            "</tr>"
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    window_to = datetime.now().strftime("%Y-%m-%d")
    window_from = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
    from datetime import timedelta
    window_from_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    top_author = authors.most_common(1)[0][0] if authors else "—"
    top_formula_key = formulas.most_common(1)[0][0] if formulas else "other"
    top_formula_label = FORMULA_LABELS.get(top_formula_key, "—")

    html_out = (tpl
        .replace("{DATE}", now)
        .replace("{WINDOW_FROM}", window_from_str)
        .replace("{WINDOW_TO}", window_to)
        .replace("{ACCOUNTS_COUNT}", str(len(following)))
        .replace("{RELEVANT_COUNT}", str(len(relevant)))
        .replace("{MEDIAN_VIEWS}", fmt_num(statistics.median(views) if views else 0))
        .replace("{MEDIAN_ER}", f"{statistics.median(ers):.2f}" if ers else "0")
        .replace("{TOP_ACCOUNT}", "@" + top_author)
        .replace("{TOP_FORMULA}", top_formula_label)
        .replace("{ROWS}", "\n".join(rows))
        .replace("{GENERATED_AT}", now)
    )

    target = out_dir / "dashboard.html"
    target.write_text(html_out)
    log.info("wrote %s (%d KB)", target, target.stat().st_size // 1024)
    return 0


if __name__ == "__main__":
    sys.exit(main())
