# Coordinator Agent

Управляет работой остальных агентов: принимает задачи, делегирует, контролирует прогресс, поднимает контент-сервисы, ведёт бэк-офис.

## Что умеет

- Делегировать задачи специализированным агентам через message-passing
- Запускать loop-coding на крупные задачи
- Поднимать контент на платформы типа AgentOS
- Делать HTML-презентации для отчётов
- Управлять памятью команды (decisions, learnings, runbooks)
- Делать ресерч перед стратегическими решениями

Coordinator — это «полу-coding + полу-content + полу-PM» гибрид. Если у тебя один Claude Code на всю операцию, он работает как coordinator.

## Скиллы

### Платформы и сайты

- [`agentos-content`](../../skills/agentos-content/) — контент для платформ AgentOS-типа (загрузка эфиров, материалов, проверки через MCP)
- [`workshop`](../../skills/workshop/) — универсальный скилл для воркшопов (Kinescope-эмбеды, таймкоды, deploy)

### Координация работы

- [`loop-coding`](../../skills/loop-coding/) — запуск больших задач через 7 фаз
- [`fast-loop-coding`](../../skills/fast-loop-coding/) — для задач 50-300 LOC
- [`cross-review`](../../skills/cross-review/) — двойное ревью перед мержем

### Ресерч и подготовка решений

- [`perplexity-research`](../../skills/perplexity-research/) — глубокий web research
- [`markdown-new`](../../skills/markdown-new/) — выжимка из доков
- [`transcript`](../../skills/transcript/) — расшифровка созвонов
- [`chat-archive`](../../skills/chat-archive/) — анализ чатов

### Отчёты и презентации

- [`present`](../../skills/present/) — главный скилл для HTML-отчётов
- [`datawrapper`](../../skills/datawrapper/) — графики и инфографика
- [`excalidraw`](../../skills/excalidraw/) — диаграммы

### Память и самообучение

- [`learnings`](../../skills/learnings/) — система Episodes → Learnings → Rules
- [`memory-audit`](../../skills/memory-audit/) — аудит файлов памяти
- [`agent-introspection`](../../skills/agent-introspection/) — самодиагностика

## Типовой coordinator-флоу

1. Принц: «нужен ресерч по рынку X»
2. Coordinator → запускает 4 параллельных Sonnet субагента через `perplexity-research`
3. Собирает их выводы, генерирует HTML-отчёт через `present`
4. Отправляет отчёт принцу в Telegram
5. Записывает решение в `learnings` (decision note) — потом другие агенты увидят

## Установка

```bash
cd ~/.claude/skills
git clone https://github.com/qwwiwi/agentos-skills-public.git agentos
for skill in agentos-content workshop loop-coding fast-loop-coding cross-review \
  perplexity-research markdown-new transcript chat-archive \
  present datawrapper excalidraw learnings memory-audit agent-introspection; do
  cp -r agentos/skills/$skill ./
done
```
