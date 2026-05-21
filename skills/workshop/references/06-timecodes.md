# 06 — Генерация таймкодов из записи эфира

Длинный эфир (2-3 часа) → структурированный список таймкодов (каждые ~4-5 минут) с заголовком каждого сегмента.

Pipeline стабилизирован после инцидента 2026-04-21 (Day-1, `.mov` сломал AssemblyAI duration detection — растягивал таймкоды в 3.337 раза).

## Ключевые правила (усвоены кровью)

1. **AssemblyAI не любит `.mov`.** Всегда конвертируй в `.mp3` перед загрузкой — иначе таймкоды будут растянуты.
2. **Полный транскрипт в контексте LLM при генерации заголовков.** Без полного текста получается generic-фигня.
3. **Язык `ru` явно.** AssemblyAI по default может угадать неправильно.
4. **Окна ~4-5 минут.** Меньше — скучно кликать, больше — не находишь нужное.

## Pipeline (3 шага)

### Шаг 1: Конвертировать видео → mp3

Входной файл может быть `.mov`, `.mp4`, `.mkv`. AssemblyAI лучше всего работает с mp3 mono 16 kHz.

```bash
ffmpeg -i input.mov \
  -vn \
  -acodec libmp3lame \
  -ar 16000 \
  -ac 1 \
  -b:a 96k \
  output.mp3
```

Флаги:
- `-vn` — drop video
- `-acodec libmp3lame` — MP3 encoder
- `-ar 16000` — 16 kHz sample rate (оптимум для speech)
- `-ac 1` — mono
- `-b:a 96k` — битрейт достаточный для речи

### Шаг 2: Транскрибировать через AssemblyAI

```python
import assemblyai as aai

aai.settings.api_key = "YOUR_KEY"  # из ~/.claude/secrets/

config = aai.TranscriptionConfig(
    language_code="ru",              # ВАЖНО: явно ru
    speech_model=aai.SpeechModel.universal,  # v2 universal-2
    punctuate=True,
    format_text=True,
)

transcriber = aai.Transcriber(config=config)
transcript = transcriber.transcribe("output.mp3")

# Сохрани JSON с words + timestamps
import json
data = {
    "text": transcript.text,
    "words": [
        {"text": w.text, "start": w.start, "end": w.end}
        for w in transcript.words
    ],
}
with open("transcript.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

Timestamps в миллисекундах от начала аудио.

### Шаг 3: Нарезать на окна и сгенерировать заголовки

Окна по ~4:26 (266 секунд) — примерно 13 блоков на 2-часовой эфир.

```python
import json
from pathlib import Path

transcript = json.loads(Path("transcript.json").read_text())
words = transcript["words"]
total_duration_ms = words[-1]["end"] if words else 0

WINDOW_MS = 266_000  # 4:26
windows = []
start = 0
while start < total_duration_ms:
    end = min(start + WINDOW_MS, total_duration_ms)
    window_words = [w for w in words if w["start"] >= start and w["end"] <= end]
    window_text = " ".join(w["text"] for w in window_words)
    windows.append({
        "start_ms": start,
        "end_ms": end,
        "text": window_text,
    })
    start = end
```

Заголовки генерируем через **Sonnet subagent** (Anthropic Max OAuth, не OpenRouter). OpenRouter для генерации текста запрещён правилом `rules.md > Model usage` — OpenRouter только для embeddings + Cognee extraction.

**Путь A (рекомендуется) — Agent tool в рамках coordinator-сессии:**

Передать весь пакет окон одним батчом в Agent tool (`subagent_type=general-purpose`, `model=sonnet`). Промпт содержит full transcript + все окна → субагент возвращает JSON `[{start_ms, title}, ...]` за один вызов. Бесплатно в рамках Max.

Системный промпт:
```
Ты редактор таймкодов для эфира EdgeLab.
Контекст полного транскрипта: {transcript_text[:50000]}
Задача: для каждого окна ниже придумать короткий заголовок (3-7 слов, по-русски, без emoji, без кавычек).
ВАЖНО: "Groq" это AI inference компания (не путать с "Grok" от xAI).
Формат ответа: строго JSON-массив [{"start_ms": N, "title": "..."}, ...] в том же порядке что и input.
```

**Путь B — CLI `claude -p` для скрипта без Agent tool:**

```bash
claude -p --output-format json --model sonnet \
  --system-prompt "$(cat system.txt)" < windows.json > titles.json
```

**НЕ использовать** `openrouter.ai/api/v1/chat/completions` для заголовков — это платный путь при наличии бесплатного через Max.

## Форматирование таймкодов для вставки в HTML

```python
def fmt_ts(ms):
    """600123 ms → '10:01', 3723000 ms → '1:02:03'"""
    s = ms // 1000
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

html_parts = []
for w in windows:
    ts = fmt_ts(w["start_ms"])
    title = w["title"]
    html_parts.append(f'''
    <div style="display: flex; gap: 12px; align-items: baseline;">
      <span style="color: #E8926A; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.8125rem; white-space: nowrap; min-width: 52px;">{ts}</span>
      <span style="color: #a1a1aa; font-size: 0.875rem;">{title}</span>
    </div>'''.strip())

print("\n".join(html_parts))
```

Вставить полученный HTML в секцию `Таймкоды` на странице дня (см. `05-add-lesson-video.md` для расположения).

## EN-версия таймкодов

Русские заголовки переводи через Sonnet subagent (тем же Agent tool) с промптом: «Переведи заголовок таймкода с русского на английский, короткий стиль 3-7 слов, без emoji». Timestamps не меняются. Без OpenRouter.

## Готовые скрипты

На Mac mini (у coordinator) есть рабочие образцы в `/tmp/workshop-lesson/` (от Day-1 FINAL pipeline):

- `transcribe2.py` — конвертация + AssemblyAI v2
- `split-and-title.py` — окна + **Sonnet subagent** для заголовков (старая версия использовала OpenRouter — нужно переписать при следующем использовании)
- `replace-timecodes.py` — замена HTML-секции таймкодов в `day-N/index.html`

Если `/tmp/` очищен, пересоздай из этого гайда или попроси user прислать.

## Что НЕ делать

- Не отправлять `.mov` напрямую в AssemblyAI — будут растянутые таймкоды.
- Не генерировать заголовки без полного транскрипта в контексте — LLM будет писать общие фразы типа «Введение», «Обсуждение».
- Не использовать YouTube auto-captions — они хуже качеством, и у нас видео на Kinescope.
- Не писать `Grok` вместо `Groq` — user заметит мгновенно (это AI inference company, не xAI model).
