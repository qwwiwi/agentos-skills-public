# 02 — Дизайн-система

Бренд EdgeLab един для всех наших сайтов. Workshop использует те же токены, что `<your-domain>` и `<your-domain>/price`.

## Источник правды (полная версия)

Полная дизайн-система живёт в скилле **`<your-design-skill>`** (Thrall shared):

- `~/.claude/skills/<your-design-skill>/references/design-system.md` — цвета, шрифты, glass-card, кнопки, градиенты
- `.../tov.md` — tone of voice, правила текста
- `.../components.md` — HTML-снипеты готовых блоков

На Mac mini с coordinator: читать через SSH `ssh root@<your-staging-server-ip> "cat ~/.claude/skills/<your-design-skill>/references/<file>"`.

Ниже — только то, что специфично для воркшопа (или отличается от общебрендового).

## Палитра (бренд-токены)

| Роль | Hex | Где применяется в воркшопе |
|---|---|---|
| Фон | `#141416` | body background, `theme.colors.surface` |
| Coral (основной акцент) | `#D97757` | CTA-кнопки, заголовки-акценты, timeline-dots активных дней |
| Coral-light | `#E8926A` | градиенты, иконки оранжевые (пред-дни до релиза) |
| Gold | `#E8B98A` | endpoint-градиенты для prices |
| Green success | `#4ade80` | **бейджи «Доступно» + иконки активных дней** (важно: иконка и бейдж должны совпадать по цвету) |
| Green bg tint | `rgba(74, 222, 128, 0.08)` | фон для `claude-cornerstone` карточек |
| Yellow warn | `#facc15` | `warning-card` (жёлтые callout-блоки с призывом к действию) |
| Indigo accent | `#818cf8` | альтернативный цветовой акцент (пр. глобальный CLAUDE.md в каскаде) |
| Muted text | `#a1a1aa` | вторичный текст, описания |
| White | `#ffffff` | заголовки, ключевой текст |

## Шрифты

- **Inter** (300, 400, 500, 600, 700, 800) — всё включая заголовки
- **SF Mono / Monaco / Menlo** (fallback mono) — код, пути, команды в бейджах

Подключение:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com/3.4.17"></script>
```

## Tailwind config (стандарт воркшопа)

```html
<script>
  tailwind.config = {
    theme: {
      extend: {
        fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
        colors: {
          surface: '#141416',
          muted: '#a1a1aa',
          accent: '#D97757',
          'accent-light': '#E8926A',
        },
      },
    },
  };
</script>
```

## Компоненты воркшопа

### `.glass-card` — базовый контейнер

```css
.glass-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 16px;
}
```

### `.accent-gradient-text` — градиентный текст

```css
.accent-gradient-text {
  background: linear-gradient(135deg, #D97757, #E8926A);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### `.primary-btn` / `.nav-btn-primary` — CTA-кнопки

```css
.primary-btn {
  background: linear-gradient(135deg, #D97757, #E8926A);
  border-radius: 12px;
  color: #fff;
  font-weight: 600;
  transition: all 0.2s ease;
}
```

### Badges дней (на главной)

- `.badge-available` — зелёный «Доступно» — текущий/прошедший день
- `.badge-soon` — приглушённый оранжевый «Скоро» — будущий день
- `.badge-date` — базовый цветной пилюлька с датой

### Timeline dots (слева от карточек на главной)

- `.timeline-dot-active` — зелёная, светящаяся, для `badge-available`
- `.timeline-dot-soon` — приглушённая, для `badge-soon`

### Иконка дня — цвет должен совпадать с бейджем!

- Если день активен (`badge-available`) → иконка на `bg-green-500/10 border border-green-500/20` + `stroke="#4ade80"`
- Если день будущий (`badge-soon`) → иконка на `bg-accent/10 border border-accent/20` + `stroke="#E8926A"`

**Это правило проверяется глазами** — см. `08-learnings.md` про инцидент «ключик оранжевый» после открытия дня 2.

### `.warning-card` (жёлтый callout)

```css
.warning-card {
  background: rgba(250, 204, 21, 0.06);
  border: 1px solid rgba(250, 204, 21, 0.2);
  border-radius: 12px;
  padding: 16px 20px;
}
.warning-card p { color: #facc15; margin: 0; font-size: 0.875rem; }
```

Используется на страницах дней для «если нашёл проблему — сделай X» блоков с копируемыми промптами.

### `.claude-cornerstone` — зелёная рамка «Обязательно»

Премиум-блок для ключевых разделов, которые нельзя пропустить. Пример: блок про CLAUDE.md на День 2.

```css
.claude-cornerstone {
  background: linear-gradient(135deg, rgba(74, 222, 128, 0.08), rgba(217, 119, 87, 0.05));
  border: 1.5px solid rgba(74, 222, 128, 0.35);
  border-radius: 18px;
  padding: 26px 22px;
  box-shadow: 0 0 40px rgba(74, 222, 128, 0.08);
}
```

Внутри использует суб-компоненты: `.cs-badge`, `.cs-title`, `.cs-sub`, `.cs-cascade`, `.cs-why`, `.cs-tests`, `.cs-prompt-box`, `.cs-sources-list`. Полный набор — в `site/day-2/index.html` (образец).

### `.arch-diagram` / `.arch-agent` — responsive карточки архитектуры

Для схем «у тебя на VPS два агента: Jarvis + Richard» и подобных. Desktop 3 колонки, mobile 1fr stack через `@media (max-width: 768px)`. Не использовать ASCII-рамки — они ломаются на мобильном (см. `08-learnings.md`).

## Типографика (минимумы)

| Элемент | Tailwind-классы |
|---|---|
| H1 Hero | `text-3xl sm:text-4xl font-extrabold` |
| H2 секция | `text-xl font-bold` |
| Карточка заголовок | `text-lg font-bold` |
| Карточка тело | `text-sm text-muted` |
| Бейдж | `text-xs font-medium` |
| Код-бейдж | `text-xs` + `font-family: SF Mono` |

## TOV (tone of voice)

- Короткое тире `–` (U+2013), не `--` и не `—`.
- Русские кавычки «» для RU-контента.
- Бренд: `EdgeLab`, не `Edge Lab`. Продукт: `Edge Lab (IEL)`.
- Никаких emoji.
- Прямо, без преамбул.

## Где смотреть живой образец

- **Главная:** `site/index.html` — timeline с 4 днями, бейджи, иконки.
- **День 0:** `site/day-0/index.html` — текстовый гайд (не эфир), много warning-card.
- **День 1:** `site/day-1/index.html` — полная структура с видео, таймкодами, промптами (референс для новых дней).
- **День 2:** `site/day-2/index.html` — содержит `claude-cornerstone` блок с тестами.
- **День 3:** `site/day-3/index.html` — пустой/placeholder (будет заполняться).

При создании нового блока — сначала посмотри, нет ли такого в живом коде. Переиспользуй, не дублируй стили.
