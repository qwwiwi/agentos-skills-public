# 07 — Video lessons pipeline (Kinescope · timecodes · transcripts)

End-to-end: видео-эфир → Kinescope → транскрипт AssemblyAI → тайм-коды через Sonnet →
кнопка скачивания транскрипта на странице урока.

Этот документ — извлечённые уроки из обработки 5 уроков предобучения 2026-05-08
(б1bbbd71… b1bbbd71-…, 36ed0f3b-…, 95449b5f-…, 89713332-…, 031fb52e-…).

## Когда использовать

- Принц записал новый эфир (mp4 на Mac mini) → нужно опубликовать на платформе
- Перезаливка существующего урока (новая запись)
- Замена тайм-кодов или транскрипта без перезаписи видео

## Не использовать для

- Текстовых бонусов без видео (там `kinescope_video_id` остаётся null, кнопка
  скачивания транскрипта тоже не показывается)
- Эфиров на другом хостинге (только Kinescope — других не подключаем)

## Полный пайплайн (4 этапа)

### Этап 1 — Upload в Kinescope

```bash
set -a; source ~/.claude/secrets/kinescope.env; set +a
# KINESCOPE_API_KEY должен быть live (~36 chars)

# Один POST со всем файлом в body. X-Video-Title — b64 от ASCII placeholder,
# потому что HTTP headers ASCII-only (cyrillic title через header не пройдёт).
python3 << 'PY'
import os, json, base64, requests
KEY = os.environ["KINESCOPE_API_KEY"]
FOLDER = "acab8be8-8765-4b3c-9315-56f7b3505f36"  # AgentOS Intensive · Предобучение

n = 6  # номер урока
filepath = f"~/Уроки AgentOS/Предобучение урок {n}.mp4"
size = os.path.getsize(filepath)
b64 = lambda s: base64.b64encode(s.encode()).decode("ascii")

with open(filepath, "rb") as f:
    resp = requests.post(
        "https://uploader.kinescope.io/v2/video",
        data=f,
        headers={
            "Authorization": f"Bearer {KEY}",
            "X-Video-Title": b64(f"L{n}-tmp"),    # ASCII placeholder
            "X-File-Name": b64(f"L{n}.mp4"),
            "X-Parent-Id": FOLDER,
            "Content-Type": "video/mp4",
            "Content-Length": str(size),
        },
        timeout=(30, 1800),
    )
data = resp.json()
video_id = data["data"]["id"]
print(f"video_id={video_id}")

# PATCH правильный cyrillic title через v1 REST API (это body — JSON, кодировка OK)
patch = requests.patch(
    f"https://api.kinescope.io/v1/videos/{video_id}",
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    json={"title": "Урок 6 — Название урока"},
    timeout=30,
)
print(f"PATCH={patch.status_code}")
PY
```

**Грабли upload:**

1. **`X-Title` не работает** — Kinescope принимает только `X-Video-Title`. С `X-Title`
   валидатор отвечает HTTP 400 «title required» даже если значение есть.
2. **TUS protocol creation НЕ работает на v2/video** — POST с пустым body даёт
   «empty request body». Endpoint поддерживает только creation-with-upload (всё
   тело в одном запросе). Поэтому tusclient `create + patch` не работает.
3. **`X-Video-Title` хранится как b64-encoded строка**, Kinescope её НЕ декодит. Поэтому
   placeholder ASCII сразу + PATCH через `/v1/videos/{id}` cyrillic'ом.
4. **5 параллельных upload'ов через urllib загружали в RAM весь файл** → Broken
   pipe. Решение: `requests.post(data=f)` со streaming + sequential, не parallel.
5. **Folder UUID для AgentOS Intensive предобучения:**
   `acab8be8-8765-4b3c-9315-56f7b3505f36`. Узнать через `GET /v1/projects` →
   `data[0].folders[]`.

### Этап 2 — CSP и Caddy для iframe

**Без этого iframe рендерится чёрным экраном без сообщения** — браузер блокирует
загрузку плеера через CSP, нет visible error в UI.

В `apps/web/next.config.ts`:

```ts
const CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' ...",
  "img-src 'self' data: https://*.supabase.co https://t.me https://kinescope.io https://*.kinescope.io https://*.kinescopecdn.net",
  "style-src 'self' 'unsafe-inline'",
  "frame-src 'self' https://kinescope.io https://*.kinescope.io",
  "media-src 'self' https://*.kinescope.io https://*.kinescopecdn.net blob:",
  "frame-ancestors https://web.telegram.org https://*.telegram.org 'self'",
  "font-src 'self' data:",
  "base-uri 'self'",
].join('; ');
```

**HARD RULE:** Caddy в `/etc/caddy/Caddyfile` тоже выдаёт CSP-header — он
перезаписывает Next.js header. Всегда обновлять оба места одновременно.
Проверка: `curl -sS -I https://<your-agentos-domain>/ | grep -i content-security`
показывает Caddy-версию. На staging:3010 / prod:3020 — Next.js напрямую (через
Caddy не идёт), там CSP из next.config.ts.

После правки Caddyfile: `caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy`.

### Этап 3 — iframe в page.tsx

**Проверенный pattern для iOS Safari** (Tailwind `aspect-video` + `absolute inset-0`
+ `overflow-hidden rounded-2xl` ломает touch на iOS):

```tsx
{bonusN === null && kinescopeId && (
  <div className="mt-3 mx-4">
    <div
      style={{
        position: 'relative',
        paddingTop: '56.25%',  // 9/16
        borderRadius: '16px',
        overflow: 'hidden',
        background: '#000',
      }}
    >
      <iframe
        src={`https://kinescope.io/embed/${kinescopeId}?playsinline=1`}
        style={{
          position: 'absolute',
          top: 0, left: 0, width: '100%', height: '100%', border: 0,
        }}
        allow="autoplay; fullscreen; picture-in-picture; encrypted-media; gyroscope; accelerometer; clipboard-write; web-share"
        allowFullScreen
      />
    </div>
  </div>
)}
```

Источники для `kinescopeId`:
1. `liveOverride.dto.kinescope_video_id` (если backend вернул) — приоритет.
2. `base.kinescopeId` из mock `ONBOARDING_LESSONS[id].kinescopeId` — fallback при offline или 403.

### Этап 4 — Транскрибация через AssemblyAI

```bash
set -a; source ~/.claude/secrets/assemblyai.env; set +a

# 1. Извлечь mp3 из mp4 (ffmpeg, 16kHz mono, libmp3lame, 96k)
ffmpeg -i "~/Уроки AgentOS/Предобучение урок 6.mp4" \
  -vn -ac 1 -ar 16000 -codec:a libmp3lame -b:a 96k \
  /tmp/agentos-lessons/mp3/lesson6.mp3

# 2. Транскрибировать
python3 << 'PY'
import os, json, assemblyai as aai
aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]
config = aai.TranscriptionConfig(
    language_code="ru",
    speech_models=["universal-2"],   # ← ВАЖНО: список, не строка
    punctuate=True, format_text=True,
)
t = aai.Transcriber(config=config).transcribe("/tmp/agentos-lessons/mp3/lesson6.mp3")
out = {
    "id": t.id,
    "text": t.text,
    "duration_ms": int((t.audio_duration or 0) * 1000),
    "words": [{"text": w.text, "start": w.start, "end": w.end} for w in (t.words or [])],
}
with open("/tmp/agentos-lessons/transcripts/lesson6.json","w") as f:
    json.dump(out, f, ensure_ascii=False)
print(f"id={t.id}, duration={out['duration_ms']/60000:.1f}min, words={len(out['words'])}")
PY
```

**Грабли:**

1. **`speech_model="best"` deprecated** — теперь `speech_models=["universal-2"]` массивом.
   Если оставишь старый формат — ошибка «speech_model is deprecated» или «speech_models must be non-empty list».
2. **transcript_id остаётся в AssemblyAI account** — список доступен через
   `GET /v2/transcript?limit=10`. Не теряй id — пригодится для перевыдачи
   через AssemblyAI без повторной транскрибации.

### Этап 5 — Тайм-коды через Sonnet

```python
# Сгруппировать words по 30s окнам
import json
with open("/tmp/agentos-lessons/transcripts/lesson6.json") as f:
    t = json.load(f)
windows = []
cur_start, cur_words = None, []
for w in t["words"]:
    if cur_start is None:
        cur_start = w["start"]
    if w["start"] - cur_start >= 30000:
        windows.append({"start_ms": cur_start, "text": " ".join(cur_words)})
        cur_start, cur_words = w["start"], []
    cur_words.append(w["text"])
if cur_words:
    windows.append({"start_ms": cur_start, "text": " ".join(cur_words)})

# Сохранить и отдать Sonnet через Agent tool
import json
with open("/tmp/agentos-lessons/windows.json","w") as f:
    json.dump({"6": {"duration_ms": t["duration_ms"], "windows": windows}}, f, ensure_ascii=False)
```

Затем `Agent(subagent_type=general-purpose, model=sonnet)` с промптом:

> Прочитай windows.json. Для урока 6 сгенерируй 5-7 тайм-кодов:
> `{ts: int_seconds, label: "3-7 слов"}`. ts = start одного из windows
> где явно начинается новая тема (по сигналам «теперь про X»,
> «второе», «следующий пункт», «перейдём к»). Первый ts=0. Минимальный
> gap 30s. Запиши в `timecodes_v2.json`.

**HARD RULE:** генерация заголовков ТОЛЬКО через Agent tool с Sonnet/Opus subagent
(rules.md: «любая генерация текста — через Agent tool в рамках Anthropic Max,
никогда через OpenRouter»).

### Этап 6 — Запись в DB и mock

```python
import json, os, urllib.request
SUPABASE = os.environ["SUPABASE_MGMT_API"]
TOKEN = os.environ["SUPABASE_ACCESS_TOKEN"]

def fmt_ts(s):
    m, sec = divmod(int(s), 60)
    return f"{m:02d}:{sec:02d}"

tcs = json.load(open("/tmp/agentos-lessons/timecodes_v2.json"))["6"]
new_blocks_tcs = [
    {"id": f"timecode-{i+1}", "ts": fmt_ts(t["ts"]), "type": "timecode", "label": t["label"]}
    for i, t in enumerate(tcs)
]

# 1. Прочитать текущие blocks, удалить старые timecode, вставить новые
#    после headers (meta/outcome/skills) и перед первым step.
# 2. UPDATE intensive_lessons SET kinescope_video_id='<id>',
#    blocks=$blocks$<json>$blocks$::jsonb WHERE lesson_number=6.
# Полный скрипт см. /tmp/agentos-lessons/db_update_v2.py из 2026-05-08.
```

Параллельно — **mock в `apps/web/app/intensive/lesson/[id]/page.tsx`**:

- В `LessonMock` interface есть поле `kinescopeId?: string` — заполнить.
- В `ONBOARDING_LESSONS['6'].timecodes[]` — те же тайм-коды что в DB.
- Без mock SSR покажет старое — фронт читает DB только client-side.

### Этап 7 — Markdown транскрипт для скачивания

```python
# Делегировать Sonnet'у через Agent tool — у него есть words.json + timecodes.
# Промпт: для каждой timecode-секции [ts_i, ts_{i+1}] склеить words с этим start,
# разбить на абзацы по паузам >800ms (или принудительно каждые 4 предложения),
# сохранить как:
#
# # Урок 6 · Название
# **Курс:** AgentOS Intensive · Предобучение
# **Длительность:** MM:SS мин
# **Источник:** видео-эфир, транскрипция AssemblyAI universal-2
# ---
# ## MM:SS — Label из timecodes
# Текст абзацами…
#
# Куда: /tmp/agentos-lessons/transcripts-md/lesson-6.md
```

После — копия в `apps/web/public/transcripts/lesson-6.md` (статически
раздаётся Next.js под `/transcripts/lesson-6.md`).

### Этап 8 — Кнопка «Скачать транскрипт» на странице урока

В `app/intensive/lesson/[id]/page.tsx` между видео и таймкодами:

```tsx
{lessonN !== null && lessonN >= 1 && lessonN <= 6 && (   // ← обнови верхнюю границу
  <div className="mt-3 mx-4">
    <a
      href={`/transcripts/lesson-${lessonN}.md`}
      download={`agentos-lesson-${lessonN}-transcript.md`}
      className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border border-line bg-surface hover:border-gold-line transition-colors"
    >
      <svg className="ic text-gold-hi flex-shrink-0" width="16" height="16" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
      </svg>
      <span className="text-[13px] text-ink-1 flex-1 min-w-0">Скачать транскрипт</span>
      <span className="font-mono text-[10px] text-ink-3 flex-shrink-0">.md</span>
    </a>
  </div>
)}
```

**Условие** (`lessonN <= N`) обнови когда добавляешь новый транскрипт.

## Чеклист добавления нового видео-урока

- [ ] mp4 на Mac mini в `~/Уроки AgentOS/Предобучение урок N.mp4`
- [ ] Upload в Kinescope (этап 1) → `kinescope_video_id` сохранён в `kinescope_lN.json`
- [ ] PATCH cyrillic title через `/v1/videos/{id}`
- [ ] mp3 → AssemblyAI → `transcripts/lessonN.json` со словами и id
- [ ] windows → Sonnet → `timecodes_v2.json` с реальными ms
- [ ] DB UPDATE: `kinescope_video_id` + замена timecode-блоков
- [ ] mock UPDATE: `kinescopeId` + `timecodes[]` в page.tsx
- [ ] Sonnet → markdown транскрипт → `apps/web/public/transcripts/lesson-N.md`
- [ ] Расширить условие `lessonN <= ...` для кнопки скачивания
- [ ] CSP next.config.ts + Caddy (если впервые) → frame-src kinescope.io
- [ ] Build + atomic deploy на prod
- [ ] Visual verify (mandatory): открыть страницу урока, тапнуть на iframe — плеер играет; нажать кнопку — .md скачивается

## Связанные файлы

| Файл | Назначение |
|---|---|
| `~/.claude/secrets/kinescope.env` | `KINESCOPE_API_KEY=...` |
| `~/.claude/secrets/assemblyai.env` | `ASSEMBLYAI_API_KEY=...` |
| `~/.claude/secrets/supabase.env` | Management API token + project ref |
| `apps/web/next.config.ts` | CSP с frame-src/media-src |
| `/etc/caddy/Caddyfile` (prod server) | Caddy CSP — должен матчить next.config |
| `apps/web/app/intensive/lesson/[id]/page.tsx` | iframe + кнопка скачивания + mock |
| `apps/web/public/transcripts/lesson-N.md` | статические markdown-транскрипты |
