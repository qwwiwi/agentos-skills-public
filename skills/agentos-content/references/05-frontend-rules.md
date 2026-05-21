# 05 — Frontend rendering rules

Правила, как фронт регулирует отображение контента. Не нарушать без обсуждения с userем.

## Правило 1: видео-плеер скрыт для бонусов

```tsx
{/* video player — только для обычных уроков, не для бонусов */}
{bonusN === null && (
  <div className="...">
    {/* play button + progress bar */}
  </div>
)}
```

Файл: `apps/web/app/intensive/lesson/[id]/page.tsx`. `bonusN` приходит из `bonusNumberFromId(id)`.

**Логика:** бонусы — текстовые гайды (Mac mini setup, Stack solutions). Видео нет → плейсхолдер
с play-кнопкой не показывать.

## Правило 2: таймкоды скрыты для бонусов

```tsx
const isBonus = bonusN !== null;
const tcs = isBonus ? [] : blocks.filter((b) => b.type === 'timecode');
const rest = blocks.filter((b) => b.type !== 'timecode');
```

**Логика:** таймкоды бессмысленны без видео (00:00 / 04:00 не к чему привязаться).

⚠️ Принц явно сказал: «таймкода ставим только если есть видео либо эфир». Не нарушать.

Заметь: timecode-блоки всё равно МОГУТ быть в DB (для парности структуры) — фронт их
просто фильтрует. Не нужно удалять их из patch_db.py.

## Правило 3: ID-кнопок нет нигде

Ранее на каждом блоке (step / code / prompt / mcp_config / agent_config) была вторая
кнопка `# ID` рядом с «Копировать». Удалена — визуальный шум.

Файл: `apps/web/components/blocks/UnifiedBlockRenderer.tsx`

```tsx
function BlockRow({ block, resourceUri: _resourceUri, allBlocks: _allBlocks }: RowProps) {
  // Copy controls live ONLY on prompt / code / step / mcp_config / agent_config — content copy.
  // ID copy was removed (visual noise for end users).
  switch (block.type) {
    ...
  }
}
```

`copyId` переменная и `variant="id"` CopyButton больше НЕ нужны. Если найдёшь их в новом
коде — удаляй.

## Правило 4: «Копировать» только на интерактивных блоках

Кнопка «Копировать» (с содержимым) живёт ТОЛЬКО на:
- `step` — копирует полный текст шага (Шаг N + title + Цель + body)
- `code` — копирует код
- `prompt` — копирует промпт
- `mcp_config` — копирует JSON
- `agent_config` — копирует содержимое файла

На meta / skills / outcome / prereqs / timecode / text / github / link — копирования НЕТ.
Для них есть «Скопировать всё (Markdown)» — вверху страницы (CopyResourceLink).

## Правило 5: mockToBlocks adapter

Функция `mockToBlocks(mock)` в `page.tsx` превращает старый формат `LessonMock`
(который раньше был main API) в массив `UnifiedBlock[]`. Используется как **fallback**
если API недоступен.

Поддерживает:
- meta-duration (всегда первым)
- skills (если непустой)
- outcome (если есть)
- github (если `fullGuideHref` есть — для онбординг-уроков)
- step + code (из `mock.steps[]`)
- timecode (из `mock.timecodes[]`)
- prompt (из `mock.prompts[]`)
- github (из `mock.repos[]`)

## Правило 6: render order на странице бонуса

```
1. Page header (eyebrow + h1 title)
2. CopyResourceLink (Скопировать всё в Markdown)
3. [SKIP: timecodes] для бонусов
4. Description block
5. UnifiedBlockRenderer(rest):
   - meta (но duration=hidden если ключ === 'duration')
   - skills
   - outcome
   - steps (с code-блоками после если есть command)
   - prompts
   - github (репо-карточки)
6. Back link
```

Order соответствует `blocks[]` массиву из source-of-truth (см. `02-source-of-truth.md`).

## Правило 7: один featured prompt

`featured: true` подсвечивает промпт золотой рамкой и тегом «основной». Используй
**только для одного** промпта на урок (визуальная иерархия). Если featured > 1 —
все теряют выделение.

## Правило 8: не делай UI-only фичи

Agent Native: всё, что фронт делает с контентом, должен уметь делать и API/MCP.
Если добавляешь фичу «настроить через UI» — спроси: можно ли это сделать через
Supabase PATCH или через MCP tool? Если да — делай через API, фронт только потребитель.

## Где добавлять новые block types

1. `apps/web/lib/unified-block-types.ts`:
   - Добавь TS type `MyNewBlock`
   - Добавь в union `UnifiedBlock`
   - Добавь case в `parseBlockItem` switch (с валидацией полей)

2. `apps/web/components/blocks/UnifiedBlockRenderer.tsx`:
   - Добавь case в `BlockRow` switch
   - Создай функцию `MyNewRow({ block }: { block: MyNewBlock })`
   - Если нужна «Копировать» — используй `<CopyButton text={...} ariaLabel="..." />`

3. Source-of-truth Python: добавь массив или генератор для нового типа в `patch_db.py`
   и `update_mock.py` (если нужно показывать в SSR fallback).

4. Обнови `01-architecture.md` block-types таблицу.
