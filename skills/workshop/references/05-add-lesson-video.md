# 05 — Добавление видео-урока на страницу

Видео хостится **ТОЛЬКО на Kinescope** (не YouTube, не Vimeo — Kinescope не блокируется, быстрее по РФ, нет рекламы). Встраивается через стандартный iframe.

## Когда использовать

- Запись эфира дня → в блок `#block-0` (или новый `#video`)
- Отдельный урок/демо → в блок `#lesson`
- Bonus-видео → отдельная секция с понятным заголовком

## Стандартный паттерн встройки

Все iframe на воркшопе выглядят одинаково. Копируй этот блок:

```html
<div class="glass-card overflow-hidden">
  <div style="position: relative; padding-top: 56.25%;">
    <iframe
      src="https://kinescope.io/embed/VIDEO_ID"
      allow="autoplay; fullscreen; picture-in-picture; encrypted-media; gyroscope; accelerometer; clipboard-write; web-share"
      frameborder="0"
      allowfullscreen
      style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    </iframe>
  </div>
</div>
```

- `padding-top: 56.25%` — это 16:9 соотношение (`9 / 16 = 0.5625`). Не меняй если видео снято обычно.
- `VIDEO_ID` — UUID из Kinescope (из URL встройки). Пример: `1d3f9902-336c-4d06-acdc-361e93ace845`.

## Пошагово: как получить embed-URL

1. Зайти на `kinescope.io` (логин через почту EdgeLab).
2. Загрузить видео (drag-and-drop). Дождаться окончания транскодирования.
3. Открыть видео → **Поделиться** → **Встраивание**.
4. Скопировать iframe целиком, ИЛИ только `VIDEO_ID` из поля `src`.
5. Вставить в HTML страницы по шаблону выше.

## Видео + таймкоды (единый блок)

Типичная структура на странице дня:

```html
<section id="block-0" class="max-w-3xl mx-auto px-4 sm:px-6 pb-8">
  <div class="glass-card overflow-hidden">
    <!-- 1. iframe -->
    <div style="position: relative; padding-top: 56.25%;">
      <iframe src="https://kinescope.io/embed/ID" ... ></iframe>
    </div>

    <!-- 2. Optional: warning-block (если были техпроблемы на эфире) -->
    <div style="margin: 16px 20px 0; padding: 14px 16px; background: rgba(220,160,50,0.08); border: 1px solid rgba(220,160,50,0.25); border-radius: 10px;">
      <p style="font-weight: 600; color: rgba(220,160,50,0.9); font-size: 0.8125rem; margin: 0 0 6px;">Внимание: технические сложности</p>
      <p style="margin: 0; color: #a1a1aa; font-size: 0.8125rem; line-height: 1.6;">...</p>
    </div>

    <!-- 3. Таймкоды -->
    <div style="padding: 20px 24px; border-top: 1px solid rgba(255,255,255,0.06); margin-top: 16px;">
      <p style="color: #fff; font-weight: 600; font-size: 0.875rem; margin: 0 0 12px;">Таймкоды</p>
      <div style="display: flex; flex-direction: column; gap: 6px;">
        <!-- Каждый таймкод: -->
        <div style="display: flex; gap: 12px; align-items: baseline;">
          <span style="color: #E8926A; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.8125rem; white-space: nowrap; min-width: 52px;">0:00</span>
          <span style="color: #a1a1aa; font-size: 0.875rem;">Описание блока</span>
        </div>
      </div>
    </div>
  </div>
</section>
```

Таймкоды генерируются отдельным pipeline — см. `06-timecodes.md`.

## Автоматика: embed в RU + EN

Когда добавляешь видео — ВСЕГДА парой в обе версии. Embed-URL **одинаковый** (Kinescope не имеет локализации видео). Меняются только русский/английский тексты таймкодов и предупреждений.

```html
<!-- site/day-N/index.html (RU) -->
<p>...Таймкоды...</p>

<!-- site/en/day-N/index.html (EN) — тот же iframe, другой текст -->
<p>...Timecodes...</p>
```

## Что проверить после deploy

1. Видео грузится на `/day-N/` и `/en/day-N/`.
2. iframe responsive (на мобильном не вылезает за рамки).
3. Нет `X-Frame-Options: DENY` ошибок в консоли (Kinescope не блокирует встраивание на чужих доменах — если ошибка, проверь правильность `VIDEO_ID`).
4. Если видео приватное — убедись что оно `unlisted` или `public` в Kinescope (иначе зрители не увидят).

## Что НЕ делать

- Не встраивать YouTube/Vimeo — бренд-правило EdgeLab.
- Не писать собственный player — используй Kinescope iframe.
- Не выставлять `width="560" height="315"` на iframe — нужен responsive через `padding-top: 56.25%`.
- Не добавлять автоплей без надобности — раздражает зрителя.
