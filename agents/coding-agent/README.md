# Coding Agent

Пишет код больших задач: миграции, рефакторинги, MCP-серверы, REST API, DevOps. Делает code review. Чинит серверы.

## Что умеет

- 7-фазный пайплайн для больших задач (loop-coding)
- 4-фазный пайплайн для средних (fast-loop-coding)
- Создание MCP-серверов на Python/Node
- Дизайн REST API + конвертация в MCP
- Двойное ревью (Opus + Codex)
- Аудит и починка Linux/macOS серверов
- Самообучение через episodes/learnings

## Скиллы

### Большие задачи кода

- [`loop-coding`](../../skills/loop-coding/) — главный скилл, 7 фаз (Research → Audit → Plan → Implement → Review → Fix-loop → Ship)
- [`fast-loop-coding`](../../skills/fast-loop-coding/) — облегчённая версия для задач 50-300 LOC

### MCP и API

- [`mcp-builder`](../../skills/mcp-builder/) — создание MCP-серверов (Python/Node), 4-фазный процесс
- [`mcp-api-build`](../../skills/mcp-api-build/) — дизайн REST API по Google AIP / Stripe / Anthropic MCP Spec, конвертация в MCP

### Ревью

- [`cross-review`](../../skills/cross-review/) — двойное ревью двумя моделями параллельно

### DevOps

- [`dev-pipeline`](../../skills/dev-pipeline/) — оркестрация разработки на удалённом сервере
- [`server-doctor`](../../skills/server-doctor/) — аудит и починка Linux/macOS, mapping процессов, диагностика инцидентов

### Самообучение

- [`learnings`](../../skills/learnings/) — система Episodes → Learnings → Rules
- [`memory-audit`](../../skills/memory-audit/) — аудит файлов памяти
- [`agent-introspection`](../../skills/agent-introspection/) — самодиагностика агента

### Ресерч и подготовка

- [`perplexity-research`](../../skills/perplexity-research/) — research best practices, libraries, patterns
- [`markdown-new`](../../skills/markdown-new/) — выжимка из доков

## Типовой coding-флоу (большая задача)

1. Принц: «сделай миграцию X»
2. `loop-coding` запускается → Phase 1 Research (Sonar + Sonnet + GitHub-scout параллельно)
3. Phase 2 Audit — Codex GPT-5.5 ищет существующие решения, оценивает риски
4. Phase 3 Plan — Codex GPT-5.5 пишет архитектурный план + brief для тестов
5. Phase 4 Implement — Opus субагенты пишут код, после каждого коммита запускаются тесты
6. Phase 5 Review — Codex + Opus параллельно ревьюят, скрипты мерджат findings
7. Phase 6 Fix-loop — максимум 3 итерации, иначе эскалация принцу
8. Phase 7 Ship — git push автоматически, staging автономно, production только с явным «да, на prod»

## Установка

```bash
cd ~/.claude/skills
git clone https://github.com/qwwiwi/agentos-skills-public.git agentos
for skill in loop-coding fast-loop-coding mcp-builder mcp-api-build cross-review \
  dev-pipeline server-doctor learnings memory-audit agent-introspection \
  perplexity-research markdown-new; do
  cp -r agentos/skills/$skill ./
done
```

## Что НЕ должен делать coding-agent

- Не пишет контент (для этого [marketing-agent](../marketing-agent/))
- Не делает production deploy без явного approval
- Не лезет в чужие repos без задачи от координатора
