# 05 — Грабли Miro API

Если что-то падает — проверь этот список.

## 1. Bulk create limit

`layout_create` валится с `HTTP 400 Bulk create failed` на ≥14 items.

| Items в одном вызове | Результат |
|---|---|
| 1–12 | OK |
| 13 | OK (на грани) |
| 14+ | HTTP 400 на части или всех |

**Workaround:** разбивай на группы по 9–12 items. Большие шаги (Антипаттерны на 20 items) — два sequential вызова на тот же frame.

⚠️ **Не параллель** два вызова на один frame. Race → fail.

```
# OK
layout_create на frame A (10 items)  ↓ wait
layout_create на frame A (8 items)   ↓ wait

# OK (параллель)
layout_create на frame A (10 items)  ─┐
layout_create на frame B (10 items)  ─┘ in parallel

# FAIL
layout_create на frame A (10 items)  ─┐
layout_create на frame A (8 items)   ─┘ parallel = race
```

## 2. Символ ✕ (U+2715) ломает API

Любой TEXT с символом `✕` падает HTTP 400, независимо от размера батча.

**Замены:**
- `—` (em-dash, U+2014) — лучше всего вписывается в editorial стиль
- `×` (multiplication sign, U+00D7) — если нужен явный X
- `X` (latin) — последний вариант

Другие безопасные символы для маркеров: `•`, `→`, `·`, `+`.

## 3. HTML entity escape

В DSL некоторые символы парсятся как HTML entities, в `result_dsl` возвращаются escaped:

| В input | В result_dsl |
|---|---|
| `+` | `&#43;` |
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `=` | `&#61;` |

Это **косметика отображения** в DSL view. На canvas Miro отображает правильный символ. Но при `layout_update` с `old_string` — нужно использовать **escaped версию** (как в result_dsl), не оригинал.

Пример:
```
# Создал
t TEXT ... "Цель + Контекст + Роль"

# Хочу обновить
# WRONG (не сматчит):
old_string = "Цель + Контекст + Роль"

# RIGHT:
old_string = "Цель &#43; Контекст &#43; Роль"
```

## 4. Параллельные вызовы на один frame = race

Уже упоминал в #1 но повторю — это самая частая причина «странных» fail'ов.

При параллельных layout_create на одном frame:
- API получает два запроса одновременно
- В обоих case `Bulk create failed: HTTP 400`
- Items не создаются (или создаются частично с непредсказуемым результатом)

Sequential на тот же frame работает чисто:
```
# Step 1
mcp__miro__layout_create frame=A items=10 → OK
# Step 2 (после step 1)
mcp__miro__layout_create frame=A items=8 → OK
```

## 5. layout_update scope

При `layout_update` без `moveToWidget` — match идёт только по top-level items (FRAMES + items не в frame). Children frames **не видны** в этом scope.

Если хочешь обновить child frame:
```
# WRONG
mcp__miro__layout_update miro_url=BOARD old_string="x=300 y=140 ..." new_string="..."
# Не сматчит, потому что текст внутри frame

# RIGHT
mcp__miro__layout_update miro_url=BOARD?moveToWidget=<F1_ID> old_string="x=300 y=140 ..." new_string="..."
```

## 6. Удаление frame с children

`layout_update old_string="<FRAME line>" new_string=""` — удаляет **только frame**. Children остаются на board как orphan items с прежними **board-absolute** координатами.

Если хочешь снести всё (frame + children):
1. `layout_read miro_url=...?moveToWidget=<frame_id>` — получи DSL
2. `layout_update` каждый child item на пустую строку
3. `layout_update` сам frame на пустую строку

Или быстрый способ через Miro UI: select frame → Delete → confirm «delete with children».

## 7. После Convert to Slides

Когда принц делает Convert to Slides на фрейме:
- Frame превращается в slide widget
- API доступ к этому фрейму **частично ломается**
- `layout_read?moveToWidget=<frame_id>` может вернуть «Item not found»
- Children тексты остаются доступными для **редактирования через Miro UI**, но через API правки могут не применяться

**Правило:** все API-правки делать **до** Convert to Slides. После — только UI.

## 8. SHAPE с border_width=0

Если хочешь shape без border (просто filled rectangle), нельзя `border_width=0`:

```
# FAIL — HTTP 400 «border_width=0.0 must be greater than 0»
shape SHAPE x=100 y=100 w=200 h=100 fill=#c8a24a border_width=0
```

**Workaround:** `border_width=1` + `border_opacity=0` (border invisible).

```
shape SHAPE x=100 y=100 w=200 h=100 fill=#c8a24a border_width=1 border_opacity=0 fill_opacity=1
```

## 9. SHAPE с h=2 (тонкая декоративная линия)

Если делаешь hairline под title (тонкая золотая черта):
```
hr SHAPE x=300 y=320 w=80 h=2 fill=#c8a24a fill_opacity=1 border_width=1 border_opacity=1 border_color=#c8a24a
```

Иногда падает HTTP 400 в bulk batch. Если фейлит — создавай отдельным вызовом, или вообще без декоративной hairline (текстовая иерархия достаточно).

## 10. Image widgets в frame для Convert to Slides

`image_create` с `moveToWidget=<frame_id>` создаёт image внутри frame с relative координатами. Но Miro **Convert to Slides** не подхватывает image widgets в слайдовый режим — они появляются на board, но НЕ в slide deck.

Если нужна картинка на финальном слайде:
- Принц вставит вручную при записи (face-cam справа + при необходимости ссылка на screenshot)
- Или: добавить image **после** Convert to Slides через Miro UI

## Prevention checklist (перед каждым layout_create)

- [ ] ≤12 items per call
- [ ] `moveToWidget=<frame_id>` если работаю внутри frame
- [ ] Координаты relative (если moveToWidget) в `0..frame.w / 0..frame.h`
- [ ] Нет символа `✕` в текстах
- [ ] Sequential per frame, параллель только разные frames
- [ ] Если `+` `=` `&` в тексте — учти escape при будущих updates
