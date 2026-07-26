#!/usr/bin/env python3
"""Generate 15 ТЗ HTML from top-15 reels.

Usage: python3 10-gen-tz.py <output_dir>
Reads: <output_dir>/state/reels-top15.json, <skill_root>/templates/tz-reel.html
Writes: <output_dir>/tz-01.html … tz-15.html
"""
from __future__ import annotations

import html
import json
import os
import logging
import random
import re
import sys
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("reel-radar.10")

FORMULA_LABELS = {
    "stop_doing": "STOP doing X",
    "you_didnt_know": "Ты не знал",
    "step_guide": "Пошаговый гайд",
    "hack": "Лайфхак",
    "provocation": "Провокация",
    "comparison": "Сравнение",
    "warning": "Предостережение",
    "other": "Инсайт",
}

# Example code words + the lead magnet each one unlocks. Replace with your own:
# the pair is (что зритель пишет в комментах, что он за это получает).
# Override for a whole batch via FORCE_CTA_CODE / FORCE_CTA_BENEFIT env vars,
# or point CODE_WORDS_FILE at a JSON file [["СЛОВО", "бенефит"], ...].
DEFAULT_CODE_WORDS = [
    ("ГАЙД", "пошаговый гайд по теме ролика"),
    ("ШАБЛОН", "готовый шаблон, который я показал"),
    ("СПИСОК", "список инструментов из видео"),
    ("ЛИСТ", "чек-лист на одну страницу"),
    ("РАЗБОР", "разбор кейса целиком"),
    ("СТАРТ", "инструкцию для старта с нуля"),
    ("СХЕМА", "схему процесса в PDF"),
    ("ПЛАН", "недельный план внедрения"),
]


def load_code_words() -> list[tuple[str, str]]:
    """Read code words from $CODE_WORDS_FILE, falling back to the examples above."""
    path = os.environ.get("CODE_WORDS_FILE", "").strip()
    if not path:
        return DEFAULT_CODE_WORDS
    try:
        raw = json.loads(Path(path).read_text())
        pairs = [(str(w).strip(), str(b).strip()) for w, b in raw if str(w).strip()]
        return pairs or DEFAULT_CODE_WORDS
    except (OSError, ValueError, TypeError):
        return DEFAULT_CODE_WORDS


CODE_WORDS = load_code_words()


def fmt_num(n: float | int) -> str:
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n/1_000:.1f}K".replace(".0K", "K")
    return str(n)


def detect_theme(text: str) -> str:
    t = text.lower()
    checks = [
        (("claude", "клод"), "Claude Code"),
        (("cursor",), "Cursor"),
        (("gpt", "chatgpt", "openai"), "ChatGPT"),
        (("mcp",), "MCP"),
        (("n8n",), "n8n"),
        (("zapier",), "Zapier"),
        (("make.com", "make "), "Make.com"),
        (("agent", "агент"), "AI-агенты"),
        (("no-code", "no code", "нокод"), "No-code"),
    ]
    for keys, label in checks:
        if any(k in t for k in keys):
            return label
    return "AI"


def build_headline(reel: dict) -> str:
    cap = reel.get("caption", "") or ""
    first_line = cap.split("\n", 1)[0].strip()
    if first_line and len(first_line) < 90:
        return first_line
    theme = detect_theme(cap)
    return f"Рилс про {theme} — {fmt_num(reel.get('play_count',0))} просмотров"


def _is_mostly_cyrillic(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    cyr = sum(1 for c in letters if "\u0400" <= c <= "\u04FF")
    return cyr / len(letters) >= 0.5


TO_BE_ADAPTED_MARK = (
    '<p><strong>[TO_BE_ADAPTED_BY_CLAUDE]</strong> '
    'Телесуфлёр = <b>перевод транскрипта оригинала на русский</b>, не пересказ. '
    'Берёшь фразы по порядку, переводишь, подставляешь свой tone of voice. '
    'Продукт/инструмент/шаги остаются 1-в-1. '
    '<b>Единственное что меняется по содержанию – CTA</b>: оригинальный призыв '
    'автора (comment X / link in bio / и т.д.) заменяется на наш код-слово + бенефит. '
    '<b>CTA = ПОСЛЕДНИЙ АБЗАЦ этого же телесуфлёра</b> (см. строку .cta-bridge ниже) '
    'с плавным неразрывным переходом из контента рилса в код-слово – не отдельным '
    'блоком. Структура единого текста: хук → контент → CTA, без склейки. '
    'См. разделы «Правило 1-в-1» и «CTA вшит в телесуфлёр» в SKILL.md.</p>'
)


def teleprompter_from_transcript(transcript: str, caption: str) -> str:
    """Render transcript as teleprompter stub.

    Hard rule (см. SKILL.md «Правило 1-в-1»): телесуфлёр воспроизводит
    концепт оригинала 1-в-1 (тот же продукт / инструмент / workflow).
    Адаптация = язык + свой tone of voice + CTA-кодослово. Формулы не подставлять.

    Эта функция только рендерит то, что уже есть в транскрипте. Если
    транскрипт пуст, слишком короткий или не по-русски – ставит маркер
    [TO_BE_ADAPTED_BY_CLAUDE] и сырой транскрипт в <details>.
    Итоговый текст дописывается Claude руками по транскрипту.
    """
    base = transcript.strip() if transcript and len(transcript) > 40 else caption.strip()
    if not base:
        log.warning("teleprompter: empty transcript/caption – flagging for manual adaptation")
        return TO_BE_ADAPTED_MARK
    base = base.replace("\u2014", "\u2013")  # em-dash -> en-dash
    if not _is_mostly_cyrillic(base):
        log.warning("teleprompter: non-Russian transcript – flagging for manual adaptation (len=%d)", len(base))
        return (
            TO_BE_ADAPTED_MARK
            + '<details><summary>Сырой транскрипт оригинала (перевести и переписать 1-в-1)</summary>'
            + f'<p>{html.escape(base)}</p></details>'
        )
    sentences = re.split(r"(?<=[.!?])\s+", base)
    chunks = []
    current = []
    char_count = 0
    for s in sentences:
        current.append(s)
        char_count += len(s)
        if char_count > 220:
            chunks.append(" ".join(current))
            current = []
            char_count = 0
    if current:
        chunks.append(" ".join(current))
    return "\n".join(f"<p>{html.escape(c)}</p>" for c in chunks if c.strip())


def build_timeline(formula: str, duration_sec: float) -> str:
    dur = max(15, min(int(duration_sec) or 30, 60))
    if formula == "stop_doing":
        blocks = [
            (0, 3, "<b>Хук:</b> «Хватит делать X – вот почему это убивает твой прогресс»"),
            (3, 8, "<b>Аргумент:</b> конкретный пример где X проваливается"),
            (8, max(9, dur - 7), "<b>Решение:</b> показать Y – что работает вместо X, с экраном"),
            (max(9, dur - 7), dur, "<b>CTA:</b> код-слово в комментах + ссылка в профиле"),
        ]
    elif formula == "step_guide":
        blocks = [
            (0, 3, "<b>Хук:</b> «За 30 секунд покажу как [результат]»"),
            (3, 10, "<b>Шаг 1:</b> настройка инструмента"),
            (10, 20, "<b>Шаг 2:</b> главное действие – запись экрана"),
            (20, max(21, dur - 5), "<b>Шаг 3:</b> результат и проверка"),
            (max(21, dur - 5), dur, "<b>CTA:</b> код-слово → подробный гайд в ЛС"),
        ]
    elif formula == "you_didnt_know":
        blocks = [
            (0, 3, "<b>Хук:</b> «Ты не знал, что [инструмент] умеет [фича]»"),
            (3, 8, "<b>Контекст:</b> как думал большинство"),
            (8, max(9, dur - 7), "<b>Раскрытие:</b> демо скрытой фичи на экране"),
            (max(9, dur - 7), dur, "<b>CTA:</b> код-слово за подборку таких фич"),
        ]
    elif formula == "hack":
        blocks = [
            (0, 3, "<b>Хук:</b> «Один хак – и [метрика] ×10»"),
            (3, 6, "<b>Проблема:</b> что было до"),
            (6, max(7, dur - 7), "<b>Хак:</b> что сделать, шаги на экране"),
            (max(7, dur - 7), dur, "<b>CTA:</b> код-слово → список таких хаков"),
        ]
    else:
        blocks = [
            (0, 3, "<b>Хук:</b> цепляющая фраза – в первые 3 секунды зритель решает"),
            (3, 10, "<b>Проблема:</b> обозначить боль зрителя"),
            (10, max(11, dur - 10), "<b>Решение:</b> демо / кейс / скриншот"),
            (max(11, dur - 10), max(dur - 5, 15), "<b>Доказательство:</b> цифры или результат"),
            (max(dur - 5, 15), dur, "<b>CTA:</b> код-слово в комментах"),
        ]
    parts = []
    for start, end, text in blocks:
        parts.append(
            f'<div class="tb"><div class="t">{start:02d}–{end:02d}s</div><div class="d">{text}</div></div>'
        )
    return "\n".join(parts)


def pick_codeword(i: int) -> tuple[str, str]:
    # env override: force same CTA for all TZ (e.g. FORCE_CTA_CODE=WORKSHOP)
    forced_code = os.environ.get("FORCE_CTA_CODE", "").strip()
    forced_benefit = os.environ.get("FORCE_CTA_BENEFIT", "").strip()
    if forced_code:
        return (forced_code, forced_benefit or "материалы по теме")
    return CODE_WORDS[i % len(CODE_WORDS)]


def build_cta_bridge(code_word: str, benefit: str) -> str:
    """Closing paragraph of the teleprompter — CTA вшит в сам текст, не отдельный блок.

    Hard rule (SKILL.md «CTA вшит в телесуфлёр»): призыв звучит как ПОСЛЕДНИЙ абзац
    телесуфлёра с плавным переходом из контента рилса в код-слово. Это default,
    не опция. Lead-in («И это лишь часть системы...») — generic fallback; Claude
    ОБЯЗАН переписать его под содержание конкретного рилса, чтобы переход был
    неразрывным (связка «это только верх айсберга / один из десятков / такую
    команду под себя» цепляет CTA к теме). Env FORCE_CTA_BRIDGE_LEAD задаёт lead-in.
    """
    lead = os.environ.get("FORCE_CTA_BRIDGE_LEAD", "").strip() or "И это лишь часть системы."
    return (f"{html.escape(lead)} Хочешь собрать такое под себя – напиши "
            f"<b>{html.escape(code_word)}</b> в комментах, {html.escape(benefit)}.")


def why_hit(reel: dict, formula: str) -> str:
    views = int(reel.get("play_count", 0))
    er = float(reel.get("engagement_rate", 0))
    formula_label = FORMULA_LABELS.get(formula, "—")
    ref_code = (reel.get("relevance_meta") or {}).get("best_ref_code", "")
    lines = [
        f"Формула <b>{html.escape(formula_label)}</b> – проверенный шаблон, зритель цепляется за хук в первые 3 секунды.",
        f"Просмотры <b>{fmt_num(views)}</b> при ER <b>{er}%</b> – пик внимания к теме <b>{html.escape(detect_theme(reel.get('caption','')))}</b>.",
    ]
    if ref_code:
        lines.append(f'Похожая подача залетала у тебя в рилсе <a href="https://www.instagram.com/reel/{html.escape(ref_code)}/" target="_blank">{html.escape(ref_code)}</a> – адаптация под твой блог высоковероятна.')
    return "<br>".join(lines)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) < 2:
        log.error("usage: 10-gen-tz.py <output_dir>")
        return 2
    out_dir = Path(sys.argv[1])

    reels = json.loads((out_dir / "state" / "reels-top15.json").read_text())
    tpl = (SKILL_ROOT / "templates" / "tz-reel.html").read_text()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for i, r in enumerate(reels, 1):
        formula = (r.get("relevance_meta") or {}).get("formula", "other")
        formula_label = FORMULA_LABELS.get(formula, "Инсайт")
        code_word, cw_benefit = pick_codeword(i - 1)
        theme = detect_theme(r.get("caption", ""))
        transcript = r.get("transcript", "")

        rendered = (tpl
            .replace("{TZ_NUM}", f"{i:02d}")
            .replace("{FORMULA_LABEL}", html.escape(formula_label))
            .replace("{HEADLINE}", html.escape(build_headline(r)))
            .replace("{SOURCE_URL}", html.escape(r.get("url", "")))
            .replace("{SOURCE_AUTHOR}", html.escape(r.get("author", "")))
            .replace("{TOPIC}", html.escape(theme))
            .replace("{RELEVANCE_SCORE}", str(r.get("relevance_score", 0)))
            .replace("{VIEWS}", fmt_num(r.get("play_count", 0)))
            .replace("{LIKES}", fmt_num(r.get("like_count", 0)))
            .replace("{COMMENTS}", fmt_num(r.get("comment_count", 0)))
            .replace("{ER}", str(r.get("engagement_rate", 0)))
            .replace("{WHY_HIT}", why_hit(r, formula))
            .replace("{TELEPROMPTER}", teleprompter_from_transcript(transcript, r.get("caption", "")))
            .replace("{CTA_BRIDGE}", build_cta_bridge(code_word, cw_benefit))
            .replace("{TIMELINE}", build_timeline(formula, r.get("video_duration", 30)))
            .replace("{CTA_TEXT}", f"Код-слово в финале (звучит в телесуфлёре, дубль на экран):")
            .replace("{CODE_WORD}", html.escape(code_word))
            .replace("{CW_BENEFIT}", html.escape(cw_benefit))
            .replace("{DURATION}", f"{float(r.get('video_duration',0)):.1f}")
            .replace("{KEYWORDS}", " ".join(f'<span class="pill">{html.escape(k)}</span>' for k in (r.get("matched_keywords") or [])[:8]))
            .replace("{GENERATED_AT}", now)
        )

        path = out_dir / f"tz-{i:02d}.html"
        path.write_text(rendered)
        log.info("wrote %s (%d KB)", path, path.stat().st_size // 1024)

    return 0


if __name__ == "__main__":
    sys.exit(main())
