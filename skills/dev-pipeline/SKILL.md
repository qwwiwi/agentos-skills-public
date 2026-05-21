---
name: dev-pipeline
description: Dev Pipeline v4 -- полный цикл разработки. Codex аудит/план → Coder субагент пишет код → Claude+Codex cross-review → Coder фиксит → результат user. Вызывай когда user даёт задачу на код.
version: 4.0.0
---

# Dev Pipeline v4

Полный цикл: аудит → план → код → ревью → фикс → результат.
Каждая фаза -- статус user. Он видит что происходит.

## Когда использовать
- Принц дал задачу на код (фича, баг, рефакторинг)
- Задача >5 строк кода
- Нужен аудит перед изменениями

## Роли

| Роль | Кто | Модель |
|------|-----|--------|
| Координатор | Сильвана (я) | Opus 4.6 |
| Аудитор | Codex CLI | GPT-5.5 |
| Планировщик | Codex CLI | GPT-5.5 |
| Кодер | Coder субагент | Opus 4.6 |
| Ревьюер 1 | Сильвана | Opus 4.6 |
| Ревьюер 2 | Codex CLI | GPT-5.5 |

## Pipeline

### Фаза 1: АУДИТ (Codex)

**Статус user:** `[1/5] Аудит -- Codex анализирует текущее состояние`

```bash
cd <git-repo-dir> && codex exec --model gpt-5.5 "Audit the current state of <target>. Report: architecture, dependencies, potential issues, risks." 2>&1
```

Если не git-repo -- передать содержимое через stdin.
Показать user краткие findings (3-5 пунктов).

### Фаза 2: ПЛАН (Codex)

**Статус user:** `[2/5] План -- Codex проектирует решение`

```bash
cd <git-repo-dir> && codex exec --model gpt-5.5 "Based on audit: <findings>. Task: <description>. Write implementation plan: files, changes, tests, risks." 2>&1
```

Показать план user. Ждать одобрения. Если корректирует -- обновить.

### Фаза 3: КОД (Coder субагент)

**Статус user:** `[3/5] Код -- Coder (Opus) реализует план`

```
Agent(subagent_type="coder", prompt="<полное ТЗ с планом, файлами, конвенциями>")
```

Если задач несколько независимых -- параллельно (макс 5).
Показать user: какие субагенты запущены, что делают.

### Фаза 4: CROSS-REVIEW (Claude + Codex)

**Статус user:** `[4/5] Ревью -- Claude + Codex проверяют код`

Claude: баги, безопасность, соответствие плану, конвенции.
Codex: `codex review --uncommitted` или diff через stdin.
Показать user: таблица findings.

### Фаза 5: ФИКС (если нужен)

**Статус user:** `[5/5] Фикс -- Coder исправляет N замечаний`

Critical/warning: `Agent(subagent_type="coder", prompt="Fix: <findings>")`
Только info: пропускаем.

### РЕЗУЛЬТАТ

**Статус user:** `Готово`

Финальный отчёт: задача, файлы, аудит, ревью (critical/warning/info), тесты, что проверить.

## Правила

1. Статус `[N/5]` на каждой фазе
2. Аудит обязателен
3. План показать user, ждать одобрения
4. Coder != reviewer
5. Два ревьюера (Claude + Codex) всегда
6. Фикс через coder, не самой
7. Микрофиксы (<5 строк) -- без pipeline

## Быстрый режим (1 файл, <30 строк)

1. Сама читаю файл (аудит)
2. Coder пишет
3. Claude review
4. Готово

## Интеграция

| Фаза | Superpowers скилл |
|------|-------------------|
| План | writing-plans |
| Код (>3 задач) | subagent-driven-development |
| Код | test-driven-development |
| Ревью | requesting-code-review |
| Верификация | verification-before-completion |
| Мерж | finishing-a-development-branch |
| Дебаг | systematic-debugging |

## Safe Deploy (обязательный контракт с 2026-04-17)

Причина: инцидент 2026-04-17 — HTML в кэше ссылался на удалённые чанки → 404 → Caddy на проде отдавал их с `max-age=31536000, immutable` → страница мёртвая на год в браузере ученика.

### Серверная сторона (Caddy)

Для ЛЮБОГО сайта где есть `handle /_next/static/*` с `header_down Cache-Control "...immutable"`:

```caddyfile
# Ошибки НИКОГДА не immutable. Без defer Caddy пишет заголовок до статуса.
@errors status 4xx 5xx
header @errors Cache-Control "no-store, no-cache, must-revalidate" {
    defer
}

# HTML: всегда revalidate (свежие имена чанков)
@html_response header Content-Type "text/html*"
header @html_response Cache-Control "private, no-cache, must-revalidate" {
    defer
}
```

Hard rule: после любого деплоя Caddy — `curl -I` на несуществующий static-путь. Ожидание: `no-store`. Если `immutable` — откат немедленно.

### Клиентская сторона (Next.js)

1. `app/global-error.tsx` — ловит ChunkLoadError, `sessionStorage`-guard от цикла, `window.location.reload()`. Один reload на сессию.
2. `next.config.ts` — `deploymentId: process.env.EDGELAB_BUILD_ID`. С Next 14.1.4 hard-nav при несовпадении версий.

### deploy.sh (releases + symlink)

Никакого `rsync` поверх `current`. Только:
- `releases/<sha>/` куда льём билд
- `ln -sfn releases/<sha> current.new && mv -T current.new current` — атомарный свитч через rename(2)
- `pm2 reload` (требует `wait_ready` в ecosystem.config.js)
- Держим 5 последних релизов: `ls -1dt releases/* | tail -n +6 | xargs -r rm -rf`
- Rollback = один `ln -sfn`

Шаблон: `core/artifacts/deploy-safe.sh`.

### Порядок раскатки

1. Staging автономно. Проверка smoke + `curl -I` на ошибки.
2. Double review (Opus + Codex GPT-5.5).
3. Prod — ТОЛЬКО с явным «да, на prod» от userа. Перед деплоем: restic snapshot на DO Spaces.
4. После prod: проверить `/`, `/dashboard`, `/auto-login?t=test`, несуществующий static — все правильно отвечают и кэшируются по правилам.
