# AgentOS Skills — Каталог скиллов для Claude Code

Production-tested скиллы от команды EdgeLab — для кодинга, ресерча, контента, продаж и AI-генерации.

Этот репозиторий — публичная часть скиллов, которые мы используем каждый день в работе агентов Orgrimmar. Опубликовано как материал для учеников интенсива AgentOS.

---

## Что такое скилл

Скилл — это компактная инструкция для Claude Code, которая активируется по триггеру. Внутри: описание задачи, пошаговый процесс, шаблоны, иногда вспомогательные скрипты. Когда ты пишешь Claude «сделай мне рилс» — он находит скилл `reels` и работает по проверенной методике.

Подробнее: [vibe.edgelab.space](https://vibe.edgelab.space)

---

## Скиллы по ролям агентов

Если хочешь увидеть готовые наборы скиллов под конкретные роли (marketing, sales, coding, coordinator, monitoring, reviewer) — смотри папку [`agents/`](./agents/). Там для каждой роли README с описанием, списком скиллов и одной командой для установки.

## Категории

| Категория | Скиллов | Что внутри |
|-----------|---------|------------|
| **Ресерч** | 10 | perplexity, twitter, transcript, markdown-new, groq-voice, reel-radar, chat-archive, topic-monitor, yt-research, telegram-chip |
| **Кодинг** | 9 | loop-coding, fast-loop-coding, mcp-builder, mcp-api-build, cross-review, dev-pipeline, server-doctor, agent-browser, senior-brainstorm |
| **Контент** | 3 | content-engine, present, seo-tune |
| **Соцсети** | 8 | instagram-superpower, carousel-instagram, reels, reels-analytics-for-brokers, youtube-producer, youtube-thumbnail, threads-content, twitter (создание) |
| **AI-генерация** | 5 | codex-image, higgsfield-generate, higgsfield-soul-id, higgsfield-product-photoshoot, higgsfield-marketplace-cards |
| **Сайты и приложения** | 2 | workshop, agentos-content |
| **Визуализация** | 3 | excalidraw, miro-board, datawrapper |
| **Системные и память** | 3 | learnings, memory-audit, agent-introspection |

Продажный блок (`crm-workflow`, `qualification`, `objection-handling`, `follow-up`) и копирайтинг лендингов пока не опубликованы — они в разделе [«Готовятся к публикации»](./CATALOG.md#готовятся-к-публикации). Роль `sales-agent` до их выхода собрана на research-скиллах, см. [`agents/sales-agent`](./agents/sales-agent/). Прогревы по Product Launch Formula лежат отдельным репозиторием: [qwwiwi/plf-walker](https://github.com/qwwiwi/plf-walker).

---

## Установка

Скиллы хранятся в `~/.claude/skills/`. Чтобы установить весь каталог:

```bash
cd ~/.claude/skills
git clone https://github.com/qwwiwi/agentos-skills-public.git agentos
```

Чтобы установить отдельный скилл — скопируй нужную папку из `agentos/skills/<name>/` в `~/.claude/skills/`.

```bash
cp -r ~/.claude/skills/agentos/skills/loop-coding ~/.claude/skills/
```

После установки запусти Claude Code и попробуй триггер на тестовой задаче.

---

## Структура репозитория

```
agentos-skills-public/
├── README.md            # этот файл
├── LICENSE              # MIT
├── CATALOG.md           # полное описание всех скиллов с триггерами
└── skills/
    ├── <skill-name>/
    │   ├── SKILL.md         # главная инструкция (с frontmatter)
    │   ├── references/      # доп. справочники (по необходимости)
    │   ├── scripts/         # вспомогательные скрипты (по необходимости)
    │   └── templates/       # шаблоны выходных файлов (по необходимости)
    └── ...
```

Каждый скилл — самодостаточная папка. Можно ставить по одному, можно весь набор.

---

## Дополнительные источники скиллов

| Источник | Описание | Установка |
|----------|----------|-----------|
| [obra/superpowers](https://github.com/obra/superpowers) | Универсальные мета-скиллы: TDD, debugging, plan-driven development | `git clone https://github.com/obra/superpowers.git ~/.claude/skills/superpowers` |
| [anthropics/skills](https://github.com/anthropics/skills) | Официальные скиллы Anthropic (skill-creator, cua-driver) | `git clone https://github.com/anthropics/skills.git ~/.claude/skills/anthropics` |
| [supabase/agent-skills](https://github.com/supabase/agent-skills) | Best practices для Supabase + Postgres | `git clone https://github.com/supabase/agent-skills.git ~/.claude/skills/supabase` |

---

## Создание своего скилла

Поставь официальный `skill-creator` от Anthropic — это скилл для создания скиллов. Он проведёт через интервью, поможет написать SKILL.md, протестировать и улучшить.

```bash
cd ~/.claude/skills
git clone https://github.com/anthropics/skills.git anthropics
```

После установки в Claude Code: «Создай скилл для <твоя задача>» — активируется skill-creator.

---

## Лицензия

MIT — используй, модифицируй, публикуй. Атрибуция к EdgeLab / AgentOS приветствуется.

---

## Контекст

Этот репозиторий — часть материалов интенсива «AgentOS» от EdgeLab. Кабинет интенсива: [vibe.edgelab.space](https://vibe.edgelab.space).
