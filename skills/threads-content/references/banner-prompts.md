# Banner Prompts — 4 шаблона для gpt-image-1

Все шаблоны опираются на the reference aesthetic: чёрный фон, 3D rendered app-style icons (rounded squares + glossy shadows), белые санс-сериф операторы (+, →, =), tech-meme aesthetic.

## Базовый стиль (вставляется в каждый промпт)

```
Style: 3D rendered tech meme banner, black background (#0A0A0A), 
glossy app-icon style elements with subtle shadows and reflections, 
rounded squares for app icons (like iOS app icon shape, 60-80px radius), 
clean white sans-serif operators (+, →, =, ×) in SF Pro Display Bold or Inter Bold, 
landscape 16:9 aspect ratio (1920x1080) or square 1:1 (1080x1080), 
balanced composition with elements aligned horizontally,
no people, no faces, no text except operators and minimal labels.
```

## Шаблон 1 — Negative Formula (X + Y = провал)

Когда: пост-разрушитель. «Делал X + Y, получил провал».

Структура: `[ICON A] + [ICON B] → [BROKEN RESULT] = [RED X]`

Промпт:

```
3D rendered tech meme banner, black background.

Layout: horizontal equation with 5 elements aligned on a single line:
1. [APP_ICON_A] — rounded square app icon, glossy 3D
2. white "+" operator
3. [APP_ICON_B] — rounded square app icon, glossy 3D
4. white "→" arrow operator
5. [BROKEN_RESULT] — visual metaphor of failure (drooping graph, sad face emoji-style, scribble, broken chain)
6. white "=" operator
7. large red "X" mark or red prohibition sign

Style: clean, minimalist, app-icon aesthetic.
No text except operators. No people. Black background only.
```

Заполни плейсхолдеры:
- `[APP_ICON_A]` — purple Obsidian crystal logo / тот инструмент, что не сработал
- `[APP_ICON_B]` — orange Claude burst logo / партнёр инструмента  
- `[BROKEN_RESULT]` — wilted plant / sad scribble / drooping line graph / cracked brain

## Шаблон 2 — Positive Formula (X + Y = win)

Когда: «вот связка которая работает».

Структура: `[ICON A] + [ICON B] = [WIN_RESULT с золотым свечением]`

Промпт:

```
3D rendered tech meme banner, black background.

Layout: horizontal equation, 5 elements:
1. [APP_ICON_A] — rounded square app icon, glossy
2. white "+" operator
3. [APP_ICON_B] — rounded square app icon, glossy
4. white "=" operator
5. [WIN_RESULT] — visual metaphor of success: rising graph line with golden glow, 
   trophy icon, golden star burst, brain with neural network glowing gold

Style: clean app-icon aesthetic, golden accent (#C2A878) on winning element only.
Black background. No text except operators.
```

## Шаблон 3 — Transformation (было → стало)

Когда: «раньше делал так, теперь так».

Структура: `[OLD_STATE] → [NEW_STATE]` с разделителем посередине.

Промпт:

```
3D rendered split banner, black background, 16:9 landscape.

Left half (50%): [OLD_STATE] — chaotic, grey, low-saturation visual 
  (messy stack of papers, tangled wires, dim 2D icons)

Center: thin vertical golden line + large white "→" arrow

Right half (50%): [NEW_STATE] — clean, golden-accented 3D
  (organized graph nodes, glowing connections, single elegant icon)

Style: dramatic before/after, golden accent (#C2A878) only on right side.
No people, no faces, no text labels.
```

## Шаблон 4 — Pure Equation (математическое уравнение)

Когда: чистая «формула успеха/провала», несколько слагаемых.

Структура: `[A] + [B] + [C] = [RESULT]` (4+ элемента).

Промпт:

```
3D rendered tech meme banner, black background, 16:9 landscape.

Horizontal equation with 7 elements aligned on single baseline:
1. [ICON_1]
2. white "+" operator
3. [ICON_2]
4. white "+" operator  
5. [ICON_3]
6. white "=" operator (larger, bolder)
7. [RESULT_ICON] — larger than inputs, glowing golden

All icons rounded square app-icon style, glossy 3D, with subtle drop shadows.
Equal spacing between elements. Centered composition.
Black background (#0A0A0A). Operators in white Inter Bold.
```

## Чек-лист перед генерацией

- [ ] Выбран один из 4 шаблонов под цель поста
- [ ] Иконки конкретные (не «какой-то инструмент» — а Obsidian/Claude/Notion/MCP-spec)
- [ ] Соотношение сторон выбрано (16:9 для горизонтального Threads-баннера, 1:1 для крупного)
- [ ] Цвета: чёрный фон #0A0A0A, золотой акцент #C2A878 ТОЛЬКО на выигрышном элементе, красный — на провале
- [ ] Никаких людей, лиц, длинного текста на баннере
- [ ] Запрос на gpt-image-1 через `scripts/gen-banner.sh`

## Fallback если OpenAI billing закрыт

1. Generate manually in ChatGPT Plus (DALL-E внутри) — копируем промпт ему
2. Nano Banana 2 / Higgsfield если подключим MCP
3. Top up OpenAI billing ($10 = ~50 баннеров на gpt-image-1)
