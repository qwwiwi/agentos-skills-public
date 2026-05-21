# 04 — Координатные правила Miro DSL

Это самая частая ошибка. Прочитай прежде чем что-то создавать.

## TL;DR

| Тул | Без `moveToWidget` | С `moveToWidget=<frame_id>` |
|---|---|---|
| `layout_create` | x/y **АБСОЛЮТНЫЕ** на board | x/y **ОТНОСИТЕЛЬНЫЕ** к frame top-left |
| `layout_update` | Действует на top-level board items | Действует только на children этого frame |
| `image_create` | x/y board-absolute | x/y relative to frame |
| `layout_read` | Возвращает только top-level items | Возвращает frame + его children |

## Detail: layout_create

### Без moveToWidget

```
miro_url = https://miro.com/app/board/<BOARD>=/
dsl =
f1 FRAME x=200 y=200 w=1920 h=1080 ...
t  TEXT  parent=f1 x=80 y=140 ...   ← x/y НА BOARD, не внутри frame
```

`parent=f1` в DSL — это **только логическая принадлежность** (для последующего Convert to Slides и группировки). API НЕ пересчитывает x,y относительно frame.

Если frame на `x=200..2120` и текст с `x=80, w=780` — текст окажется **слева вне фрейма** (на board x=80..860). Только последняя половина (x=200..860) перекроется фреймом, а левая часть останется на board как orphan.

### С moveToWidget

```
miro_url = https://miro.com/app/board/<BOARD>=/?moveToWidget=<F1_ID>
dsl =
t TEXT x=300 y=140 w=780 ...   ← x/y ВНУТРИ frame, top-left = (0,0)
```

Здесь `x=300` означает «300 пикселей вправо от левого края frame». На board это будет `frame.x + 300 = 200 + 300 = 500`.

x/y должны лежать в `0..frame.w` и `0..frame.h`. Outside — fail.

## Detail: layout_read

`layout_read` возвращает DSL **с виртуальной отрисовкой parent**. Когда читаешь frame children через `moveToWidget`:

```
... x=300 y=140 w=780 parent=https://...?moveToWidget=<F1_ID> ...
```

DSL показывает `x=300` как «relative within frame». Это **видимость**. На уровне Miro API координаты хранятся как **абсолютные** на board.

Доказательство: если читаешь весь board без `moveToWidget`, тот же текст возвращается с `x=500` (= board absolute). Без parent (frame удалён → orphan).

Это значит:

- `layout_read с moveToWidget` показывает **relative** view
- `layout_read без moveToWidget` показывает **absolute** view (но frame children обычно не возвращаются — only top-level)

## Detail: layout_update

`layout_update` matchит DSL текстом. Scope зависит от moveToWidget:

- `с moveToWidget=<frame_id>` → match только child items этого frame (видны в relative-view DSL)
- `без moveToWidget` → match только top-level items (FRAMES сами и items не-внутри-frame)

Поэтому если хочешь массово сдвинуть тексты внутри frame:
```
layout_update miro_url=...?moveToWidget=<F1_ID> old_string="x=80 y=" new_string="x=300 y=" replace_all=true
```

И если хочешь удалить frame (с children как orphan):
```
layout_update miro_url=... (без moveToWidget) old_string="<full FRAME line>" new_string=""
```

## Detail: image_create

```
mcp__miro__image_create
miro_url = .../?moveToWidget=<frame_id>
x=1100 y=7 width=800 image_url=...
```

С `moveToWidget` координаты **relative**. Картинка сядет внутри frame на (1100, 7). Должна влезть в frame.w/h.

Без `moveToWidget`:
```
mcp__miro__image_create
miro_url = .../  (без moveToWidget)
x=2200 y=337 width=1100 image_url=...
```

Координаты — абсолютные на board.

## История 2026-05-07 (как мы наступили на эти грабли)

Принц попросил собрать урок 5. Я сделала layout_create без moveToWidget с DSL вида:

```
f1 FRAME x=200 y=200 w=1920 h=1080 ...
t  TEXT parent=f1 x=80 y=140 w=780 ...
```

Думала: «parent=f1 значит x относительный к frame, x=80 = padding 80 inside». Реально текст оказался на board x=80, слева от фрейма. Принц прислал скриншот «текст съехал».

Решали путём fix через layout_update:
- x=80 → x=280 (добавили frame.x = 200) — частично fix
- Принц «ещё на 400» → x=680 (правее, чтоб text не ехал левой границей по фрейму)
- Принц «100 обратно» → x=580
- Принц «ещё 80» → x=500 ← финальная позиция

После этого выяснилось: при использовании `moveToWidget=<frame_id>` в layout_create — координаты **relative**. То есть если бы я сделала так с самого начала:

```
miro_url = .../?moveToWidget=<frame_id>
dsl =
t TEXT x=300 y=140 w=780 ...
```

— текст сел бы на абсолют x=500 сразу, без правок.

Конклюзия: **всегда используй moveToWidget при создании TEXT внутри frame**. Это автоматически делает координаты relative и понятными.

## Mental model

Думай о Miro API так:

- Board — бесконечный 2D холст с (0,0) в центре, абсолютные координаты у всех виджетов
- FRAMES — это просто rectangles с `type=frame` и логическими children. Дети — отдельные виджеты, координаты которых **board-absolute**, parent — лишь ссылка
- `moveToWidget` в URL — **синтаксический сахар**: говорит API «работай в системе координат этого frame». API делает translate `(x_relative, y_relative) → (frame.x + x, frame.y + y)` при create/read

Если запутался — всегда читай через `layout_read` с `moveToWidget` и проверяй фактические значения.
