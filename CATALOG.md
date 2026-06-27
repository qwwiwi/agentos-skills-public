# Каталог скиллов

Production-tested скиллы для Claude Code. Здесь — sanitize-версия наших внутренних скиллов: вычищены приватные токены, IP-адреса, личные пути, упоминания закрытых чатов.

> Каталог-витрина с подробным описанием каждого скилла живёт на [agentos.edgelab.su/intensive/5](https://agentos.edgelab.su/intensive/5).

---

## Ресерч и сбор данных

| Скилл | Что делает | Статус |
|-------|------------|--------|
| `perplexity-research` | Web research через Sonar API с источниками | available |
| `twitter` | Чтение X/Twitter через FxTwitter + SocialData | available |
| `markdown-new` | Чистое извлечение текста из URL в markdown | available |
| `transcript` | Транскрибация через AssemblyAI universal-2 | available |
| `groq-voice` | Транскрибация через Groq Whisper | available |
| `chat-archive` | Анализ архивов Telegram-чатов | available |
| `telegram-chip` | Telegram user-аккаунт (Telethon): чтение, отправка и экспорт чатов через единый HTTP API | available |
| `topic-monitor` | Регулярный мониторинг темы | available |
| `yt-research` | YouTube-ресерч: поиск по нише, velocity, скан каналов-конкурентов, транскрипты | available |

## Кодинг и разработка

| Скилл | Что делает | Статус |
|-------|------------|--------|
| `loop-coding` | 7-фазный пайплайн больших задач кода | available |
| `fast-loop-coding` | Облегчённая версия для средних задач | available |
| `mcp-builder` | Создание MCP-серверов (Python/Node) | available |
| `mcp-api-build` | Дизайн REST API + конвертация в MCP | available |
| `cross-review` | Двойное ревью Opus + Codex | available |
| `dev-pipeline` | Оркестрация разработки на сервере | available |
| `server-doctor` | Аудит и починка Linux/macOS | available |

## Контент и копирайтинг

| Скилл | Что делает | Статус |
|-------|------------|--------|
| `content-engine` | Tone-of-voice aware двигатель контента | available |
| `present` | HTML-презентации в стиле EdgeLab | available |

## Соцсети — Instagram, Reels, YouTube, Threads

| Скилл | Что делает | Статус |
|-------|------------|--------|
| `instagram-superpower` | Посты и карусели для Instagram | available |
| `reels` | Сценарии Reels — 5 форматов | available |
| `youtube-producer` | YouTube long-form | available |
| `threads-content` | Контент для Threads | available |

## AI-генерация изображений и видео

| Скилл | Что делает | Статус |
|-------|------------|--------|
| `higgsfield-generate` | Генерация в Higgsfield | available |
| `higgsfield-soul-id` | Свой персонаж через Soul ID | available |
| `higgsfield-product-photoshoot` | Продуктовая съёмка | available |
| `higgsfield-marketplace-cards` | Карточки для маркетплейсов | available |

## Сайты и приложения

| Скилл | Что делает | Статус |
|-------|------------|--------|
| `workshop` | Универсальный скилл для воркшопов | available |
| `agentos-content` | Контент для платформ типа AgentOS | available |

## Визуализация

| Скилл | Что делает | Статус |
|-------|------------|--------|
| `excalidraw` | Диаграммы Excalidraw | available |
| `miro-board` | Доски Miro через API | available |
| `datawrapper` | Графики и инфографика | available |

## Системные и память

| Скилл | Что делает | Статус |
|-------|------------|--------|
| `learnings` | Система самообучения (Episodes → Rules) | available |
| `memory-audit` | Аудит файлов памяти | available |
| `agent-introspection` | Самодиагностика агента | available |

---

## Готовятся к публикации

Эти скиллы пока в работе — sanitize требует переработки или скилл специфичен под конкретный кейс.

- `reel-radar` — анализ трендовых рилсов конкурентов
- `landing-page-copywriter` — копирайтинг лендингов
- `plf-walker` — Product Launch Formula прогрев
- `crm-workflow`, `qualification`, `objection-handling`, `follow-up` — продажный блок

---

## Условные обозначения

- **available** — скилл доступен в `skills/<name>/`
- **pending** — скилл в очереди на публикацию (sanitize → review → push)
- **deprecated** — скилл устарел, использовать альтернативу

## Как ставить

### Весь каталог

```bash
cd ~/.claude/skills
git clone https://github.com/qwwiwi/agentos-skills-public.git agentos
```

### Отдельный скилл

```bash
cp -r ~/.claude/skills/agentos/skills/<name> ~/.claude/skills/
```

После установки запусти Claude Code и проверь триггер.

## Как читать SKILL.md

Каждый скилл — самодостаточная папка:

```
<skill-name>/
├── SKILL.md         # frontmatter (name + description) + методика
├── references/      # доп. справочники (по необходимости)
├── scripts/         # вспомогательные скрипты (по необходимости)
└── templates/       # шаблоны (по необходимости)
```

В `SKILL.md` сверху YAML-блок:

```yaml
---
name: skill-name
description: "Что делает + триггеры активации"
---
```

Description — главный механизм триггеринга. Claude Code загружает все frontmatter'ы скиллов в контекст и подбирает по релевантности.

## Sanitize

Все приватные данные вычищены:
- API-ключи и токены → placeholder'ы `<YOUR_API_KEY>`
- IP-адреса наших серверов → `<your-server-ip>`
- Домены EdgeLab/наших проектов → `<your-domain>`
- Личные пути из `~/.claude-lab/` → `~/.claude/skills/`
- Telegram ID и handles → `<your-telegram-id>`
- Имена внутренних агентов → generic роли (coordinator-agent, coder-agent и т.д.)

Если найдёте остаточную утечку — откройте issue.
