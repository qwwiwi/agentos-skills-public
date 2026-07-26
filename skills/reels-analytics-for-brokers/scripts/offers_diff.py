#!/usr/bin/env python3
"""Steps 6-7: extract offers from a snapshot, then diff snapshots to see what is rising.

An offer in this niche lives about three to four weeks. By the time it is
obviously everywhere it is already spent. A single scan cannot tell you where an
offer sits on that curve — only two scans can. So every run writes an offers
snapshot, and the next run compares against it.

Two modes:
  extract  top-reels.json (+ optional transcripts) -> offers.json
  diff     previous offers.json + current offers.json -> offers-diff.{json,md}

The extractor is deliberately dumb and deterministic: regex over captions and
transcripts. It gets you a first pass you can trust to be reproducible. Reading
the leftovers in "no_cta" by hand is where the interesting findings usually are.

Usage:
  python3 offers_diff.py extract --out runs/2026-07-26 [--transcripts runs/2026-07-26/teardowns]
  python3 offers_diff.py diff --previous runs/2026-07-12 --current runs/2026-07-26
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
import sys
from datetime import date
from pathlib import Path
from typing import Any

log = logging.getLogger("offers")

# "Напиши СЛОВО в комменты", "пиши слово ЖК", "Кодовое слово: ИПОТЕКА".
# The verb is matched case-insensitively — captions normally start with a capital
# letter — but the captured code word stays case-SENSITIVE on purpose. Code words
# are shouted in caps; letting the group match lowercase would happily capture
# ordinary words like "мне" out of "напиши мне в директ".
CTA_PATTERNS = [
    re.compile(r"(?i:напиш\w+|пиш\w+|отправ\w+|скинь\w*|коммент\w*)\s+[«\"']?([A-ZА-ЯЁ][A-ZА-ЯЁ0-9]{2,})[»\"']?", re.UNICODE),
    re.compile(r"(?i:кодов\w+\s+слов\w+|слово)\s*[:\-—]?\s*[«\"']?([A-ZА-ЯЁ][A-ZА-ЯЁ0-9]{2,})[»\"']?", re.UNICODE),
]
# Standalone shouty token — how most code words actually appear in captions.
CAPS_TOKEN = re.compile(r"\b([A-ZА-ЯЁ][A-ZА-ЯЁ0-9]{3,15})\b")
# A CTA verb anywhere in the text is what licenses the bare-caps fallback below.
CTA_VERB = re.compile(r"(?i:напиш|пиш|отправ|скинь|коммент|забирай|лови|жми|получ)", re.UNICODE)
# Two tiers, because the two paths deserve different levels of trust.
#
# Tier 1 applies even to an explicit "напиши X": if the caption says "напиши в
# ДИРЕКТ", the captured word is a channel, not an offer.
CHANNEL_STOPWORD_PREFIXES = (
    "DIRECT", "ДИРЕКТ", "INSTAGRAM", "TELEGRAM", "WHATSAPP", "ЛИЧК", "СООБЩЕНИ",
    "КОММЕНТ", "ОТВЕТ",
)
# Tier 2 applies ONLY to the bare-caps fallback, where there is no verb vouching
# for the word. Matched as PREFIXES: Russian is inflected, so a nominative-only
# list filters МОСКВА but happily invents an offer called МОСКВЕ from the next
# caption. Category words live here and NOT in tier 1 — "напиши ИПОТЕКА" is a
# perfectly good code word, a bare shouted "ИПОТЕКА" is just a topic label.
CAPS_STOPWORD_PREFIXES = CHANNEL_STOPWORD_PREFIXES + (
    "REELS", "TIKTOK", "YOUTUBE", "MOSCOW", "RUSSIA", "SALE", "NEW",
    "МОСКВ", "РОССИ", "ПИТЕР", "СПБ", "СОЧИ", "КРАСНОДАР", "ЖКХ", "НДФЛ", "ИНН",
    "ОГРН", "ТОП", "НОВОСТ", "СРОЧНО", "ВНИМАНИ", "АКЦИ", "СКИДК", "ХИТ", "ВАЖНО",
    "КВАРТИР", "НОВОСТРОЙ", "ИПОТЕК",
)
LEAD_MAGNETS = [
    "гайд", "чек-лист", "чеклист", "подборк", "разбор", "консультац", "база",
    "таблиц", "шаблон", "инструкц", "калькулятор", "смет", "план", "экскурс",
]
LINK_IN_BIO = re.compile(r"(ссылк\w+\s+(в\s+)?(шапк|био|профил)|link\s+in\s+bio)", re.IGNORECASE | re.UNICODE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract offers and diff snapshots.")
    sub = parser.add_subparsers(dest="mode", required=True)

    extract = sub.add_parser("extract", help="build offers.json from a finished run")
    extract.add_argument("--out", type=Path, required=True)
    extract.add_argument("--transcripts", type=Path, help="teardown dir with <code>/transcript.txt files")

    diff = sub.add_parser("diff", help="compare two runs")
    diff.add_argument("--previous", type=Path, required=True)
    diff.add_argument("--current", type=Path, required=True)
    diff.add_argument("--fading-threshold", type=float, default=0.75,
                      help="spike ratio below which an offer counts as fading")
    return parser.parse_args()


def is_stopword(token: str, prefixes: tuple[str, ...] = CAPS_STOPWORD_PREFIXES) -> bool:
    """True when the token is a channel, place, hype word or category label."""
    upper = token.upper()
    return any(upper.startswith(prefix) for prefix in prefixes)


def extract_code_word(text: str) -> str | None:
    """Pull the code word a viewer is told to send, if there is one.

    Only the explicit "verb + WORD" forms are trusted here. The bare-caps
    fallback lives in classify() behind a CTA-verb check, because on its own it
    turns any shouted word — a city, "СРОЧНО", a brand — into an offer, and the
    offer key is what the whole radar groups by. A key made of caption noise
    makes offers appear and vanish between snapshots for no real reason.
    """
    for pattern in CTA_PATTERNS:
        match = pattern.search(text)
        if match:
            token = match.group(1).upper()
            # Only channel words are rejected here — the verb already vouched
            # for this token being the thing the viewer must send.
            if not is_stopword(token, CHANNEL_STOPWORD_PREFIXES):
                return token
    return None


def classify(text: str) -> tuple[str, str]:
    """Return (offer_key, cta_type) for one reel's text."""
    code_word = extract_code_word(text)
    if code_word:
        return code_word, "code_word"

    # Lead magnets are checked before the loose fallback: "Скачай ЧЕКЛИСТ" is a
    # lead magnet, not a code word named ЧЕКЛИСТ.
    lowered = text.lower()
    for magnet in LEAD_MAGNETS:
        if magnet in lowered:
            return f"магнит:{magnet}", "lead_magnet"
    if LINK_IN_BIO.search(text):
        return "ссылка-в-био", "link_in_bio"

    # Last resort: a shouted token, but only when the caption actually asks for
    # something. Without a CTA verb a capitalised word is just a capitalised word.
    if CTA_VERB.search(text):
        for token in CAPS_TOKEN.findall(text):
            if not is_stopword(token):
                return token.upper(), "code_word"
    return "no_cta", "none"


def snapshot_date(run_dir: Path) -> str:
    """Date of the snapshot, taken from the run folder name when it looks like one.

    Runs live in ``runs/YYYY-MM-DD``. Reading the date from the folder means a
    re-extraction of an old run stays labelled with the day it was collected
    instead of today, which matters because the whole point is comparing days.
    """
    name = run_dir.resolve().name
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", name):
        return name
    return date.today().isoformat()


def do_extract(args: argparse.Namespace) -> int:
    source = args.out / "top-reels.json"
    if not source.exists():
        log.error("no top-reels.json in %s — run rank_reels.py first", args.out)
        return 2
    reels = json.loads(source.read_text(encoding="utf-8"))
    groups: dict[str, dict[str, Any]] = {}

    for reel in reels:
        text = reel.get("caption") or ""
        if args.transcripts and reel.get("code"):
            transcript = args.transcripts / reel["code"] / "transcript.txt"
            if transcript.exists():
                text = f"{text}\n{transcript.read_text(encoding='utf-8', errors='replace')}"
        key, cta_type = classify(text)
        group = groups.setdefault(key, {
            "offer": key, "cta_type": cta_type, "reels": [], "accounts": set(),
            "spikes": [], "views": [], "first_posted": reel["posted"], "last_posted": reel["posted"],
        })
        group["reels"].append({"code": reel["code"], "url": reel["url"], "account": reel["account"],
                               "posted": reel["posted"], "views": reel["views"], "spike": reel["spike"]})
        group["accounts"].add(reel["account"])
        group["spikes"].append(reel["spike"])
        group["views"].append(reel["views"])
        group["first_posted"] = min(group["first_posted"], reel["posted"])
        group["last_posted"] = max(group["last_posted"], reel["posted"])

    offers = []
    for group in groups.values():
        offers.append({
            "offer": group["offer"],
            "cta_type": group["cta_type"],
            "n_reels": len(group["reels"]),
            "n_accounts": len(group["accounts"]),
            "accounts": sorted(group["accounts"]),
            "median_spike": round(statistics.median(group["spikes"]), 2),
            "median_views": round(statistics.median(group["views"]), 1),
            "total_views": sum(group["views"]),
            "first_posted": group["first_posted"],
            # Seeded here, then carried forward by every later diff so an offer's
            # true age accumulates instead of resetting each run.
            "first_seen": group["first_posted"],
            "last_posted": group["last_posted"],
            "examples": sorted(group["reels"], key=lambda r: -r["spike"])[:5],
        })

    offers.sort(key=lambda o: (-o["n_accounts"], -o["median_spike"]))
    snapshot = {"snapshot_date": snapshot_date(args.out), "offers": offers}
    (args.out / "offers.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    no_cta = next((o for o in offers if o["offer"] == "no_cta"), None)
    log.info("extracted %d offer groups from %d reels", len(offers), len(reels))
    if no_cta:
        log.info("NB: %d reels (%s total views) carry no detectable CTA — that is usually the biggest finding",
                 no_cta["n_reels"], f"{no_cta['total_views']:,}")
    return 0


def do_diff(args: argparse.Namespace) -> int:
    for run_dir in (args.previous, args.current):
        if not (run_dir / "offers.json").exists():
            log.error("no offers.json in %s — run `offers_diff.py extract --out %s` first", run_dir, run_dir)
            return 2
    previous = json.loads((args.previous / "offers.json").read_text(encoding="utf-8"))
    current = json.loads((args.current / "offers.json").read_text(encoding="utf-8"))
    prev_by_key = {o["offer"]: o for o in previous["offers"]}
    cur_by_key = {o["offer"]: o for o in current["offers"]}

    def born(offer: dict[str, Any]) -> str:
        """When this offer was first observed, across the whole snapshot chain."""
        return offer.get("first_seen") or offer["first_posted"]

    rows: list[dict[str, Any]] = []
    for key, offer in cur_by_key.items():
        before = prev_by_key.get(key)
        if not before:
            status, spike_delta, accounts_delta = "NEW", None, offer["n_accounts"]
            first_seen = born(offer)
        else:
            spike_delta = round(offer["median_spike"] - before["median_spike"], 2)
            accounts_delta = offer["n_accounts"] - before["n_accounts"]
            spike_ratio = offer["median_spike"] / before["median_spike"] if before["median_spike"] else 99.0
            # An offer being dropped by the accounts that ran it is the clearest
            # death signal there is — louder than the spike, which stays flat
            # right up to the end. Without this branch a 9 -> 2 collapse fell
            # into the else and got labelled PEAK, i.e. the opposite of the truth.
            collapsing = accounts_delta < 0 and abs(accounts_delta) >= 0.3 * max(before["n_accounts"], 1)
            if accounts_delta > 0 and spike_delta >= 0:
                status = "RISING"
            elif collapsing or spike_ratio < args.fading_threshold:
                status = "FADING"
            else:
                status = "PEAK"
            # Age accumulates: without this the recorded birth date can never be
            # older than one diff interval, and offer lifetime is unmeasurable.
            first_seen = min(born(before), born(offer))

        offer["first_seen"] = first_seen
        rows.append({
            "offer": key, "status": status, "cta_type": offer["cta_type"],
            "n_accounts": offer["n_accounts"], "accounts_delta": accounts_delta,
            "median_spike": offer["median_spike"], "spike_delta": spike_delta,
            "first_seen": first_seen, "last_posted": offer["last_posted"],
            "example": offer["examples"][0]["url"] if offer["examples"] else "",
        })

    for key, before in prev_by_key.items():
        if key not in cur_by_key:
            rows.append({
                "offer": key, "status": "DEAD", "cta_type": before["cta_type"],
                "n_accounts": 0, "accounts_delta": -before["n_accounts"],
                "median_spike": 0.0, "spike_delta": -before["median_spike"],
                "first_seen": born(before), "last_posted": before["last_posted"], "example": "",
            })

    # Persist the carried-forward birth dates so the NEXT diff inherits them too.
    (args.current / "offers.json").write_text(
        json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    order = {"RISING": 0, "NEW": 1, "PEAK": 2, "FADING": 3, "DEAD": 4}
    rows.sort(key=lambda r: (order.get(r["status"], 9), -r["n_accounts"]))

    result = {"previous": previous["snapshot_date"], "current": current["snapshot_date"], "offers": rows}
    (args.current / "offers-diff.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# Динамика офферов: {previous['snapshot_date']} -> {current['snapshot_date']}",
        "",
        "RISING — забирать сейчас. NEW — проверить, рано. PEAK — окно закрывается. FADING/DEAD — не трогать.",
        "",
        "| Оффер | Статус | Аккаунтов | Δ аккаунтов | Медиана всплеска | Δ всплеска | Впервые | Пример |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        spike_delta = "—" if row["spike_delta"] is None else f"{row['spike_delta']:+.2f}"
        lines.append(
            f"| `{row['offer']}` | {row['status']} | {row['n_accounts']} | {row['accounts_delta']:+d} | "
            f"{row['median_spike']:.2f}x | {spike_delta} | {row['first_seen']} | {row['example']} |"
        )
    (args.current / "offers-diff.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    rising = [r["offer"] for r in rows if r["status"] in ("RISING", "NEW")]
    log.info("wrote %s", args.current / "offers-diff.md")
    log.info("rising/new: %s", ", ".join(rising) or "none")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    return do_extract(args) if args.mode == "extract" else do_diff(args)


if __name__ == "__main__":
    sys.exit(main())
