# 01 — Architecture: lessons, bonuses, block types

## Lesson vs bonus

Платформа AgentOS имеет два типа контента:

- **Lessons (онбординг + эфиры)** — обычные уроки с видео-плеером и таймкодами.
- **Bonuses (текстовые гайды)** — без видео, без таймкодов. Установка / setup / справочники.

## ID mapping (важно — не очевидно)

URL `/intensive/lesson/{id}` использует строковый id. Маппинг ↔ DB:

| URL id | Type | bonus_number | DB row example |
|---|---|---|---|
| `/intensive/lesson/10` | bonus | **1** | "Подготовка Mac mini к роли AI-сервера" |
| `/intensive/lesson/11` | bonus | **2** | "Готовые стек-решения для проектов" |
| `/intensive/lesson/12` | bonus | **3** | "Источники трендов и ресурсов" |
| `/intensive/lesson/1..9` | regular lesson | — | онбординг + эфиры |

Маппинг определён в `apps/web/app/intensive/lesson/[id]/page.tsx`:

```typescript
function bonusNumberFromId(id: string): number | null {
  if (id === '10') return 1;
  if (id === '11') return 2;
  if (id === '12') return 3;
  return null;
}
```

Когда добавляешь новый бонус — обнови эту функцию + добавь запись в `BONUS_LESSONS` объект.

## Block types (полный список)

Из `apps/web/lib/unified-block-types.ts`:

| Type | Назначение | На странице бонуса |
|---|---|---|
| `meta` | пара ключ-значение (например, duration) | да |
| `skills` | tag-список «скиллы» | да |
| `outcome` | bullets «что получишь» | да |
| `prereqs` | bullets «перед просмотром» | редко |
| `step` | пошаговая инструкция (num + title + goal + body + resources) | **главное** |
| `code` | block кода с подсветкой и копированием | как часть step (см. SOT) |
| `prompt` | копируемый промпт (label + text + featured) | да |
| `github` | карточка репо (slug + desc) | да |
| `link` | внешняя ссылка (href + label + kind) | редко |
| `timecode` | пара (ts, label) | **скрыто на бонусах** |
| `video` | видео-плеер | **скрыто на бонусах** |
| `transcript` | ссылка на транскрипт | редко |
| `mcp_config` | копируемый MCP server конфиг (name + transport + url) | редко |
| `agent_config` | копируемый файл-конфиг агента (file + content) | редко |
| `text` | свободный markdown-текст | редко |

## Render order на странице

1. Page header (eyebrow + title)
2. Video player — **только если `bonusN === null`**
3. Meta info
4. Copy resource link (вся страница как markdown — кнопка вверху)
5. Timecodes section — **только если `bonusN === null`**
6. Description block
7. Все остальные блоки в порядке из `blocks[]` (skills, outcome, steps, prompts, repos, etc.)
8. Back link

Логика в `app/intensive/lesson/[id]/page.tsx` секция «timecodes — выносим перед описанием»
+ «video player — только для обычных уроков, не для бонусов».

## Data flow при загрузке страницы

```
URL /intensive/lesson/10
   │
   ├─ SSR: lookupLesson(id) → mock from BONUS_LESSONS['10']
   │     → mockToBlocks(mock) → блоки для первого рендера
   │
   └─ Client mount: useEffect()
         └─ apiClient.get('/api/platform/intensive/bonus/1', token)
              ├─ HTTP 200 → setApiOverride(dto)
              │     → re-render: parseUnifiedBlocks(dto.blocks) ← из Supabase
              └─ HTTP 401/403/404/abort → mock остаётся
```

**Следствия:**

- Mock — fallback. Если API упал, юзер видит mock. Поэтому mock и DB должны быть синхронизированы (см. `02-source-of-truth.md`).
- Client-side override = «миллисекунда мигания» — пользователь сначала видит mock, потом контент из API. Если в DB старая версия — будет видно, как новый контент исчезает. См. Pitfall #2 в `06-pitfalls.md`.

## Backend (для контекста)

- API `/api/platform/intensive/bonus/{N}` — FastAPI gunicorn на Thrall :8095
- Прокси: Caddy на prod server (`<your-agentos-domain>` block) → `reverse_proxy <your-staging-server-ip>:8095`
- Backend читает Supabase `intensive_bonuses` и возвращает row как BonusDto

Для контентных правок backend менять НЕ надо — только Supabase row.
