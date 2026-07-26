#!/usr/bin/env python3
"""Этап валидации 1-в-1 — детектор отклонений телесуфлёра от референса.

Зачем: LLM (Opus/Claude/GPT) при адаптации склонен ДОБАВЛЯТЬ отсебятину и
ТЕРЯТЬ блоки оригинала. Этот скрипт ловит детерминированные сигналы расхождения
между транскриптом референса и сгенерированным телесуфлёром, чтобы держать
сценарий максимально 1-в-1.

Что проверяет (язык-инвариантные якоря — переживают перевод EN→RU):
  1. Числа: каждое число из референса должно быть в телесуфлёре (и наоборот).
     Пропавшее число = выкинутый блок. Лишнее число = выдуманное LLM.
  2. Латинские якоря (бренды/инструменты: Claude, ChatGPT, HubSpot, Obsidian,
     GStack, Opus, Sonnet, RAG, MCP, …). Пропавший = продукт потерян/подменён
     (ок только если в expected_swaps). Лишний = LLM приплёл чужой инструмент.
  3. Соотношение объёма (слова tele / слова ref) — вне [0.65, 1.7] = вероятно
     дропнули блок или налили воды.
  4. CTA вшит: код-слово присутствует в ХВОСТЕ телесуфлёра (последние ~280 симв).

Семантический диф по предложениям (что именно добавлено/убрано) — отдельный
LLM-critic шаг (см. SKILL.md «Этап валидации»). Скрипт = детерминированный каркас.

Usage: validate-fidelity.py <pairs.json>
pairs.json = [{"id","reference","teleprompter","expected_swaps":["hubspot->amo crm"],"codeword":"ГАЙД"}]
Выход: печатает отчёт + пишет <pairs.json>.report.json. Код возврата 1, если есть FAIL.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

COMMON = {
    "the", "and", "you", "your", "this", "that", "with", "for", "are", "but", "not",
    "they", "them", "what", "when", "from", "have", "has", "had", "can", "will",
    "just", "all", "out", "now", "get", "got", "its", "his", "her", "their", "our",
    "who", "how", "why", "off", "one", "two", "use", "see", "say", "ask", "did",
    "every", "each", "into", "like", "make", "made", "more", "most", "some", "any",
    "then", "than", "also", "even", "here", "there", "want", "need", "know", "where",
    "comment", "follow", "send", "link", "bio", "video", "part", "way", "thing",
    "people", "really", "actually", "literally", "going", "gonna", "stuff", "lot",
    "create", "okay", "common", "after", "never", "lead", "rate", "ban", "click",
    "challenge", "disagree", "enough", "think", "tell", "open", "add", "let", "say",
    "first", "most", "once", "instead", "stop", "doing", "show", "good", "best",
}


def numbers(text: str) -> list[str]:
    raw = re.findall(r"\d[\d.,]*\d|\d", text)
    out = []
    for n in raw:
        n = n.rstrip(".,").replace(",", "")
        if n:
            out.append(n)
    return out


def latin_anchors(text: str) -> set[str]:
    """Бренд-якоря: проперные имена / инструменты / акронимы, которые остаются
    латиницей даже в русском телесуфлёре (Claude, ChatGPT, HubSpot, Obsidian,
    GStack, Opus, Sonnet, RAG, MCP, LLM, n8n, .pipeline). Обычные английские слова
    переводятся в кириллицу и НЕ являются якорями — их сюда не берём, иначе шум.

    Эвристика бренда: ALL-CAPS акроним, либо CamelCase/смешанный регистр, либо
    буква+цифра, либо Capitalized-токен, который НЕ встречается где-то ещё строчным
    (имена собственные строчными не пишут; обычные слова — пишут)."""
    # все строчные вхождения — чтобы отсеять Capitalized-но-обычные (Comment/This/...)
    lower_seen = {m.lower() for m in re.findall(r"\b[a-z][a-z0-9.\-]{1,}\b", text)}
    out: set[str] = set()
    for tok in re.findall(r"[A-Za-z][A-Za-z0-9.+\-]*[A-Za-z0-9]", text):
        low = tok.lower().strip(".-")
        if len(low) < 2:
            continue
        is_acro = tok.isalpha() and tok.isupper() and len(tok) >= 2
        inner_cap = bool(re.search(r"[a-z][A-Z]", tok))
        alnum_mix = bool(re.search(r"\d", tok)) and bool(re.search(r"[A-Za-z]", tok))
        dotted = "." in tok.strip(".") and tok[0].islower()  # .pipeline-style / make.com
        cap_proper = tok[0].isupper() and len(low) >= 3 and low not in lower_seen and low not in COMMON
        if is_acro or inner_cap or alnum_mix or dotted or cap_proper:
            out.add(low)
    return out


def words(text: str) -> int:
    return len(re.findall(r"\w+", text, re.UNICODE))


def swap_tokens(expected_swaps: list[str], side: int) -> set[str]:
    """expected_swaps like 'hubspot->amo crm'. side 0 = source (may vanish),
    side 1 = target (may legitimately appear as 'extra')."""
    out = set()
    for s in expected_swaps or []:
        parts = s.split("->")
        piece = parts[side] if len(parts) > side else ""
        for tok in re.findall(r"[A-Za-z][A-Za-z0-9.+\-]{2,}", piece.lower()):
            out.add(tok.lower())
    return out


def validate_one(item: dict) -> dict:
    ref, tele = item["reference"], item["teleprompter"]
    swap_src = swap_tokens(item.get("expected_swaps", []), 0)
    swap_tgt = swap_tokens(item.get("expected_swaps", []), 1)
    issues, warns = [], []

    # 1. numbers (WARN — перевод формата «108,000»→«108 тысяч» даёт ложные срабатывания; смотрит человек/LLM-critic)
    rn, tn = numbers(ref), numbers(tele)
    from collections import Counter
    rc, tc = Counter(rn), Counter(tn)
    missing_nums = sorted((rc - tc).elements())
    extra_nums = sorted((tc - rc).elements())
    if missing_nums:
        warns.append(f"числа из референса не найдены в телесуфлёре (проверь: дропнут блок или формат типа 108000→«108 тысяч»): {missing_nums}")
    if extra_nums:
        warns.append(f"числа в телесуфлёре, которых нет в референсе (проверь, не выдумано ли): {extra_nums}")

    # 2. latin anchors
    ra, ta = latin_anchors(ref), latin_anchors(tele)
    missing_anchors = sorted(a for a in (ra - ta) if a not in swap_src)
    extra_anchors = sorted(a for a in (ta - ra) if a not in swap_tgt)
    if missing_anchors:
        warns.append(f"бренды/термины из референса пропали в телесуфлёре (могли быть переведены кириллицей – проверь): {missing_anchors}")
    if extra_anchors:
        warns.append(f"латинские бренды/термины В телесуфлёре, которых НЕТ в референсе (вероятная отсебятина): {extra_anchors}")

    # 3. length ratio (EN→RU обычно сжимает; норма с запасом)
    rw, tw = words(ref), words(tele)
    ratio = round(tw / rw, 2) if rw else 0
    if ratio:
        if ratio < 0.5 or ratio > 1.8:
            issues.append(f"объём телесуфлёра/референса = {ratio}: {'вероятно дропнут блок' if ratio < 0.5 else 'вероятно отсебятина/вода'}")
        elif ratio < 0.62 or ratio > 1.6:
            warns.append(f"объём телесуфлёра/референса = {ratio} (на грани) – проверь, не сжато ли лишнее / не налито ли")

    # 4. CTA woven in tail
    cw = (item.get("codeword") or "").lower()
    tail = tele[-280:].lower()
    cta_ok = bool(cw) and cw in tail
    if cw and not cta_ok:
        issues.append(f"код-слово «{item.get('codeword')}» НЕ в хвосте телесуфлёра – CTA не вшит в конец (или вообще отсутствует)")

    verdict = "FAIL" if issues else ("WARN" if warns else "PASS")
    return {
        "id": item.get("id"), "verdict": verdict,
        "ratio": ratio, "ref_words": rw, "tele_words": tw,
        "missing_numbers": missing_nums, "extra_numbers": extra_nums,
        "missing_anchors": missing_anchors, "extra_anchors": extra_anchors,
        "cta_woven": cta_ok, "issues": issues, "warnings": warns,
    }


USAGE = (
    "usage: validate-fidelity.py <pairs.json>\n\n"
    'pairs.json = [{"id": "tz-01", "reference": "<транскрипт оригинала>", '
    '"teleprompter": "<наш текст без HTML>", "expected_swaps": ["hubspot->amo crm"], '
    '"codeword": "ГАЙД"}]\n\n'
    "Пишет <pairs>.report.json. Код возврата: 0 = все PASS/WARN, 1 = есть FAIL, 2 = ошибка ввода."
)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE, file=sys.stderr)
        return 2
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"file not found: {p}\n\n{USAGE}", file=sys.stderr)
        return 2
    try:
        items = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"{p} is not valid JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(items, list):
        print(f"{p} must contain a JSON array\n\n{USAGE}", file=sys.stderr)
        return 2
    reports = [validate_one(it) for it in items]
    (p.with_suffix(".report.json")).write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

    fails = sum(1 for r in reports if r["verdict"] == "FAIL")
    warns = sum(1 for r in reports if r["verdict"] == "WARN")
    print(f"Валидация 1-в-1: {len(reports)} ТЗ → PASS {len(reports)-fails-warns} · WARN {warns} · FAIL {fails}\n")
    for r in reports:
        mark = {"PASS": "✓", "WARN": "▲", "FAIL": "✗"}[r["verdict"]]
        print(f"{mark} [{r['verdict']}] {r['id']}  ratio={r['ratio']} cta_woven={r['cta_woven']}")
        for i in r["issues"]:
            print(f"      ✗ {i}")
        for w in r["warnings"]:
            print(f"      ▲ {w}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
