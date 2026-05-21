# 03 — Создание нового дня с нуля

Когда понадобится: добавить День 4, специальный бонус-урок, отдельный промо-лендинг внутри воркшопа.

## Решение перед стартом

1. **Нужен отдельный `day-N/`?** Если это модуль воркшопа — да. Если промо-вставка — может, просто секция на главной.
2. **RU-first или EN-first?** Всегда RU-first. EN-зеркало — потом.
3. **Есть ли видео эфира?** Если да — сначала читай `05-add-lesson-video.md` и `06-timecodes.md`.

## Пошаговый план

### 1. Копируй существующий день как образец

Лучший стартер — `site/day-1/index.html` (самый полный, с видео, таймкодами, промптами). Для текстового гайда без эфира — `site/day-0/index.html`.

```bash
cd /tmp/online-workshop-edgelab
cp site/day-1/index.html site/day-4/index.html
cp site/en/day-1/index.html site/en/day-4/index.html
```

### 2. Обнови метаданные в HTML

В `<head>`:
- `<title>День N – <Тема> – EdgeLab Воркшоп</title>`
- `<meta name="description" content="...">` — краткое описание для SEO и OG-превью

В теле:
- Языковой свитч: `<a href="/day-N/" class="lang-switch lang-active">RU</a> <a href="/en/day-N/" class="lang-switch">EN</a>`
- Hero-блок: `badge-date` с датой, H1, подзаголовок
- Все `day-1` ссылки внутри заменить на `day-N`

### 3. Добавь запись на главной

В `site/index.html` найди `<!-- Day N -->` блоки (там список дней). Вставь новую карточку ПЕРЕД или ПОСЛЕ существующих в правильном временном порядке.

Шаблон карточки:
```html
<!-- Day N -->
<div class="relative sm:pl-14">
  <div class="hidden sm:flex absolute left-[18px] top-6 timeline-dot timeline-dot-soon"></div>
  <a href="/day-N/" class="day-card-link">
    <div class="glass-card p-5 sm:p-6">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E8926A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <!-- тематический icon path -->
            </svg>
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-3 flex-wrap">
              <h3 class="font-bold text-lg">День N – Название</h3>
              <span class="badge-soon text-xs font-medium px-3 py-1 rounded-full">Скоро</span>
            </div>
            <p class="text-muted text-sm mt-1">Краткое описание 1-2 строки</p>
          </div>
        </div>
        <svg class="arrow-icon text-muted" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </div>
    </div>
  </a>
</div>
```

То же в `site/en/index.html` (EN-версия).

### 4. Зеркаль EN

Открой `site/en/day-N/index.html`, переведи весь текст. Структура HTML — строка-в-строку с RU. Названия CSS-классов не трогать.

Проверь типичные места:
- `<title>` и `<meta name="description">`
- `<html lang="en">`
- Hero H1, подзаголовок
- Все заголовки секций
- Все тексты карточек, warning-card, промптов
- Бейдж даты (тоже переведи если надо: «22 апреля» → «April 22»)

### 5. Deploy + verify

```bash
bash scripts/deploy.sh day-N    # если валидатор EN-паритета не запрещает
```

Скрипт:
- Проверит линии EN vs RU
- Создаст бэкап
- Rsync только для нового дня
- Проверит `/day-N/` и `/en/day-N/` возвращают 200

Если `day-N` не в allowlist `deploy.sh` (см. переменную `ALLOWED_TARGETS`) — допиши туда:
```bash
ALLOWED_TARGETS=("day-0" "day-1" "day-2" "day-3" "day-4" "day-all")
```
И переменная `PAGES` — добавь новые пути для verify:
```bash
PAGES=(... "/day-4/" "/en/day-4/")
```

### 6. Commit + push

```bash
git add site/ scripts/deploy.sh
git commit -m "Добавил День N – <Тема> (RU+EN) + обновил deploy allowlist"
git push origin main
```

## Пример: открыть будущий день (переключить `Скоро` → `Доступно`)

Когда день релизится:

1. В `site/index.html` (и `site/en/index.html`):
   - `badge-soon` → `badge-available`
   - `Скоро` → `Доступно` (или `Available`)
   - `timeline-dot-soon` → `timeline-dot-active`
   - Иконка: `bg-accent/10 border border-accent/20` → `bg-green-500/10 border border-green-500/20`; stroke `#E8926A` → `#4ade80`
2. Deploy `day-all` чтобы главная обновилась.

**Важно:** бейдж и иконка должны быть в одном цвете. Забыть обновить иконку — частая ошибка, user сразу замечает (см. `08-learnings.md`).

## Что НЕ делать

- Не писать CSS инлайн там, где можно добавить класс в `<style>`.
- Не копировать контент между днями без перевода смысла — каждый день про своё.
- Не добавлять новые цвета вне палитры из `02-design-system.md`.
- Не забывать EN-версию: deploy-скрипт упадёт на check-only, если линии не совпадают.
