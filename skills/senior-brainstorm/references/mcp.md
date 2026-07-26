---
last_verified: 2026-04-15
applies_to: [early-stage, growth, scale]
confidence: high
---

# MCP Integration

## Когда MCP, когда API

| Задача | MCP | API | Почему |
|--------|-----|-----|--------|
| Multi-tool AI агент (оркестрация 3+ сервисов) | Да | -- | MCP протокол для tool orchestration |
| Простой one-off запрос к API | -- | Да | API проще, меньше overhead |
| Интерактивная работа с DB в контексте | Да | -- | MCP сохраняет контекст между запросами |
| Webhook handler | -- | Да | Stateless, не нужен контекст |

## MCP-серверы для EdTech

| Сервер | Назначение | Risk model | Policy |
|--------|-----------|------------|--------|
| filesystem | Чтение файлов проекта | Read leak | Read-only by default |
| postgres | SQL запросы к БД | Data access, mutation | Read-only, write через explicit gate |
| github | PR, issues, code review | Code change, public disclosure | Review before push |
| puppeteer | E2E тесты, скрапинг | Resource abuse, XSS | Sandboxed, timeout limits |

## Security Model

- **Least privilege** -- read-only by default для всех MCP серверов
- Write access -- только после explicit gate (подтверждение)
- Credential isolation -- отдельные credentials для каждого сервера
- Sandboxing -- каждый MCP сервер в изолированном контейнере
- Audit trail -- логирование всех tool calls, inputs, outputs

## Bounded Workflows

- Schema inspection: `postgres` read-only -> schema dump -> analysis
- PR review: `github` -> diff -> `filesystem` -> context -> review
- Local reproduction: `filesystem` + `postgres` -> reproduce bug
- Doc lookup: `filesystem` -> find docs -> synthesize answer
