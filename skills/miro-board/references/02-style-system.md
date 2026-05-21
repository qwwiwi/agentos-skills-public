# 02 — Стилевая система

## Палитра

Тёмная editorial-схема, вдохновлённая премиальными журналами и Apple Keynote.

| Token | HEX | Использование |
|---|---|---|
| `--graphite` | `#0f0e0b` | Фон фреймов (`fill=#0f0e0b`). Не чисто чёрный — тёплее |
| `--gold-hi` | `#c8a24a` | Eyebrows, mono labels, → стрелки, pin quotes, акценты |
| `--gold-soft` | `#a8842e` | Если нужен второй gold для иерархии (редко) |
| `--warm-white` | `#fcfaf7` | Заголовки, основной текст |
| `--dim-grey` | `#8a8275` | Subtitles, описания, secondary content, footer |

Запрещено:
- Чисто белый `#ffffff` — выглядит холодно, не сочетается с graphite
- Чисто чёрный `#000000` — обрывает плавность фрейма
- Любые цвета вне этой палитры (синий, зелёный, красный) — ломают editorial-настроение

## Типографика

Miro DSL поддерживает следующие font tokens (актуально 2026-05-07):

| Token | Семейство | Назначение | Размеры |
|---|---|---|---|
| `eb_garamond` | EB Garamond | Serif titles | 28–80 |
| `plex_serif` | IBM Plex Serif | Italic pin quotes, акценты | 18–22 |
| `plex_mono` | IBM Plex Mono | Eyebrows, code-labels, footer | 14–24 |
| `plex_sans` | IBM Plex Sans | Bullets, описания, body | 14–24 |

### Размерная шкала

**Cover:**
- Title: `eb_garamond size=80` (или 64 если название длинное)
- Eyebrow: `plex_mono size=22`
- Subtitle: `plex_sans size=24`
- Bullets «что разберём»: `plex_sans size=22`
- Footer: `plex_mono size=14`

**Step:**
- Title: `eb_garamond size=58` (если название «Почему модель не понимает с первого раза» в две строки — 56–58; если короче 4 слов — до 64)
- Eyebrow: `plex_mono size=20–22`
- Subtitle (lead-line): `plex_sans size=22`
- Section headers (как «ПРИЧИНА 1 — НЕТ ЦЕЛИ»): `plex_mono size=22, color=gold-hi`
- Section body: `plex_sans size=22, color=warm-white`
- Pin quote: `plex_serif size=18–20, color=gold-hi`

**Анти-pattern:** `plex_sans size=18` или меньше для основного текста — нечитаемо при face-cam в записи. Минимум 20 для всего что должно читаться зрителем.

## Padding и spacing

В **relative coords** внутри 1920×1080 frame:

| Параметр | Значение | Пояснение |
|---|---|---|
| Left padding (текстовая зона) | `x=300` | = absolute `x=500` |
| Text width | `w=780` | оставляет 1060 пикс справа |
| Top padding | `y=140` (eyebrow start) | |
| Bottom padding | `y≥80` от bottom edge | |
| Title-to-subtitle gap | `200px` | y=240 → y=440 |
| Subtitle-to-content gap | `100px` | |
| Inter-section gap | `60–100px` | зависит от плотности |
| Bullet line-height | `45–50px` | для size=22 текста |
| Pin quote position | `y=900–1020` | bottom anchor |

## Outlining vs filled

**Никаких filled background blocks** на тексте. Только `fill_opacity=0.0` (transparent). Frame сам имеет `#0f0e0b` фон, текст ложится прямо на него.

Exception: если делаешь native схему на отдельном frame (не в lesson columns) — можно использовать filled rectangles для card visualization. Но для презентации урока — НЕ.

## Иконки и декорации

Скилл строит **только текстовые слайды** в стиле editorial poster. Никаких иконок, картинок, эмодзи внутри frames. Принц добавит face-cam при записи — этого достаточно визуально.

Если очень нужна декоративная hairline (тонкая золотая черта под title):
- SHAPE с `border_width=1`, `border_color=#c8a24a`, `border_opacity=1`, `fill_opacity=0`, `h=2`, `w=80–120`
- Position: `y=title_y + title_height + 20`
- ⚠️ `border_width=0` ломает API (HTTP 400). Минимум 1.

## Кириллица OK, но осторожно с символами

**Безопасные символы:** все буквы кириллицы и латиницы, цифры, `→`, `?`, `!`, `.`, `,`, `:`, `;`, `«»`, `—` (em-dash), `—` (en-dash), `+`.

**Опасные символы:**
- `✕` (U+2715, multiplication X) → ломает API HTTP 400. **Замены:** `—`, `×` (U+00D7), `X` (latin)
- `+` в DSL парсится как entity, в result_dsl возвращается как `&#43;` — это нормально, отображение OK
- Эмодзи (✨ 🔥 etc) — Miro может рендерить криво, лучше избегать в editorial стиле

## Pin quote — кривое сухое утверждение

В каждом step-фрейме есть pin quote внизу. Это **квинтэссенция шага в одной фразе ≤8 слов**. Принц предпочитает сухое и резкое:

✅ «Один и тот же промпт. Разница в деталях.»  
✅ «Ни одного из шести = качество вырастет вдвое.»  
✅ «Если можешь показать — не описывай.»  
✅ «Модели 2026 умные. Но они не телепаты.»  

❌ «В заключение хочется отметить, что...»  
❌ «Это очень важный момент для понимания темы»  
❌ «Запомните это правило, оно вам пригодится»  

Tone: констатация факта. Без призывов, без «давайте», без «помните». Italic serif (`plex_serif`).

## Cover footer

Только на Cover. Формат:

```
<your-domain>  ·  предобучение  ·  N / TOTAL
```

Где `N` — номер урока, `TOTAL` — всего уроков в курсе. Спейсинг: два пробела вокруг точек-разделителей. `plex_mono size=14, color=#8a8275`.

Для воркшопа:
```
<your-domain>  ·  день N  ·  M / TOTAL
```
