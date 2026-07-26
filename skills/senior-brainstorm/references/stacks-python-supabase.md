---
last_verified: 2026-05-11
applies_to: [early-stage, growth]
confidence: high
---

# Track C — Python + Supabase

Третий default-трек для проектов, где удобнее писать Python (data/ML, ботов, скрипты) и использовать managed BaaS.

## When to use this track

- Команда сильнее в Python чем в Node/Bun
- Проект с Telegram-ботом + админкой (Python boto frameworks зрелее)
- ML/AI компоненты (embedding, классификация, transformers)
- Простая веб-админка поверх существующих Python-скриптов
- Хочется минимум backend-кода — больше на BaaS

## When NOT to use

- Команда уже на Bun/Node — не тащите ради хайпа
- Real-time-heavy продукт (WebSocket, presence) — Node быстрее в этом
- Микросервисный bundle с десятками контейнеров (Python хуже масштабируется в k8s)
- Жёсткое требование SSR/SEO — у Python нет аналога Next.js, нужен фронт на TS

## Core Stack

| Layer | Default |
|---|---|
| Backend API | **Python 3.12+ + FastAPI 0.115+** + `uvicorn` ASGI |
| Validation | **Pydantic v2** (используется FastAPI нативно) |
| DB driver | **asyncpg** (через SQLAlchemy 2.x async или напрямую) |
| ORM (опционально) | **SQLAlchemy 2.x** или **SQLModel** (Pydantic + SQLAlchemy) или **Tortoise ORM** |
| Migrations | **Alembic** (для SQLAlchemy) или **Supabase migrations** (если работаете через Supabase CLI) |
| Bot framework | **aiogram 3.x** (async, типизированный) или python-telegram-bot v21+ |
| BaaS | **Supabase** (Postgres + Auth + Storage + Realtime + Edge Functions) |
| Frontend | **Next.js 16** (App Router) + TanStack Query или **Vite + React** |
| Tests | **pytest** + `pytest-asyncio` + `httpx.AsyncClient` |
| Format/Lint | **Ruff** (заменяет black + isort + flake8) + **mypy strict** |
| Process manager | **Uvicorn** (development) + **Gunicorn + UvicornWorker** (production) или PM2 |
| Deploy | VPS (Timeweb / Hetzner) + Caddy (TLS) + systemd, или Docker + Yandex Serverless Containers |

## Why FastAPI

- Auto-generated OpenAPI spec (Swagger UI + ReDoc из коробки)
- Pydantic-валидация без бойлерплейта
- Async-first — масштабируется под Telegram-боты с long-polling
- Performance близка к Node + Fastify
- Зрелые библиотеки для AI/ML интеграции (openai, anthropic SDK, transformers)

## Why Supabase + FastAPI вместе

Типичный паттерн:

- **Frontend** ходит **напрямую в Supabase** (Auth + чтение публичных данных, защищено RLS)
- **Бизнес-логика, мутации, agregations** — через **FastAPI** (использует service-role ключ Supabase для записи)
- **Webhooks** от Telegram / Stripe / OAuth — на FastAPI endpoints

Это даёт скорость BaaS + контроль над сложной логикой.

## Project structure (типовая)

```
my-project/
├── api/                         # FastAPI приложение
│   ├── main.py                  # entry: FastAPI app, routers
│   ├── routers/
│   │   ├── auth.py
│   │   ├── content.py
│   │   └── webhooks.py
│   ├── services/                # бизнес-логика
│   ├── models/                  # Pydantic models + SQLAlchemy
│   └── db.py                    # supabase client + SQLAlchemy engine
├── bot/                         # Telegram-бот (aiogram)
│   ├── main.py
│   ├── handlers/
│   └── middlewares/
├── migrations/                  # Alembic или supabase migrations
├── frontend/                    # Next.js или Vite (отдельный package.json)
├── scripts/                     # одноразовые: backfill, seeding
├── tests/
│   ├── api/
│   └── bot/
├── .env.example
├── pyproject.toml               # uv / poetry
└── README.md
```

## Auth strategy

| Сценарий | Решение |
|---|---|
| Auth через email/social | **Supabase Auth** (frontend получает JWT, backend валидирует через `supabase.auth.get_user(token)`) |
| Auth через Telegram | Свой flow: Telegram WebApp `initData` валидируется в FastAPI через `hmac` подпись, потом выдаёте свой JWT |
| Service-to-service (admin script → API) | FastAPI middleware с API-key (заголовок `X-API-Key`) |
| Agent-driven (MCP, скрипты) | Scoped токены через FastAPI + БД таблица `api_tokens` |

## API patterns

### Read-heavy (frontend ходит в Supabase напрямую)

```python
# Supabase RLS делает всю работу. FastAPI используется только для мутаций
# и сложной логики.
```

### Write — через FastAPI

```python
@app.post("/courses/{course_id}/enroll")
async def enroll(
    course_id: int,
    user: dict = Depends(get_current_user),  # из Supabase JWT
):
    # 1. Проверка прав, оплата, slots
    # 2. supabase.table("enrollments").insert(...)
    # 3. webhook в bot: "пользователь записался"
    # 4. log event для analytics
    return {"status": "enrolled"}
```

### Bot — отдельный процесс

```python
# bot/main.py — aiogram + long-polling или webhook
# Тот же Supabase client, та же БД, тот же authorization
# Запускается отдельным systemd unit / Docker-контейнером
```

## Real-time

Если нужен real-time (live чат, presence, обновление статусов):

- **Supabase Realtime** для row-level подписок (TanStack Query на фронте подписывается на изменения)
- **SSE через FastAPI** для server-driven событий, не привязанных к БД (прогресс long-running task)
- **WebSocket через FastAPI** (`websockets` или `socketio`) для двунаправленного — но это редкий случай в Python; для heavy real-time лучше Node + Hono

## Background jobs

| Подход | Когда |
|---|---|
| **APScheduler** | Простые cron-задачи внутри FastAPI |
| **Celery + Redis** | Production queue с retry, DLQ, scaling |
| **Procrastinate** (Python-native, PostgreSQL queue) | Не хотите Redis, всё в Postgres |
| **Supabase Cron + Edge Functions** | Регулярные задачи на стороне BaaS, без VPS |

## Testing

```python
# tests/api/test_enroll.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_enroll_flow(client: AsyncClient, test_user):
    response = await client.post(
        "/courses/1/enroll",
        headers={"Authorization": f"Bearer {test_user['token']}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "enrolled"
```

- **pytest-asyncio** для async-тестов
- **httpx.AsyncClient** для интеграционных
- **factory-boy** или **polyfactory** для тестовых данных
- Отдельная test-БД (Supabase Free tier для CI) или Postgres в Docker

## Deployment

### VPS (Timeweb / Hetzner / DO Droplet)

- Uvicorn + Gunicorn + UvicornWorker (3-4 worker'а на 2-core VPS)
- Systemd unit: `myproject.service` + `myproject-bot.service`
- Caddy для TLS (или nginx + certbot)
- PM2 как альтернатива systemd (если предпочитаете Node-стиль)

### Docker + Yandex Serverless Containers (для 152-ФЗ)

- `Dockerfile` с `python:3.12-slim` + uvicorn
- `yc serverless container revision deploy` — деплой одной командой
- Холодный старт 200-500ms, дальше — instant

### Free-tier варианты

- **Fly.io** — Python работает, $0 для маленьких проектов
- **Railway** — простой UI, $5/мес за runner
- **Render** — Python sleeps на free tier

## AI/LLM integration

Если в проекте AI-составляющая:

- **openai / anthropic Python SDK** — основной путь
- **OpenRouter** — для альтернативных моделей (Mixtral, Llama, Qwen) через один API
- **FastEmbed** — локальные embeddings без OpenAI ($0 на embeddings)
- **Sonar (Perplexity)** — для web-research через API
- **Langfuse** — observability LLM-вызовов (latency, cost, prompt versions)

## Pros vs Track A (Bun + Hono)

- Python зрелее для AI/ML/data
- Бот-фреймворки (aiogram 3, python-telegram-bot v21) опытнее Bun-аналогов
- Команда часто уже знает Python из data-задач
- FastAPI auto-OpenAPI > ручная Hono документация

## Cons vs Track A

- Холодный старт серверов Python > Node/Bun (на serverless критично)
- Меньше TypeScript-shared (фронт и бэк на разных языках, дублирование типов)
- Bundle для frontend всё равно через Node — отдельная экосистема

## Decision matrix: Track A vs Track B vs Track C

| Сценарий | Recommended track |
|---|---|
| Telegram-бот + админка | **C: Python + Supabase** |
| AI-агент с RAG | **C: Python + Supabase** (зрелые LLM библиотеки) |
| SPA + auth + БД, маленькая команда | **A: Bun + Hono + Vite + Supabase** |
| EdTech SaaS с Stripe Billing + LMS | **B: Node + Fastify + Next.js** |
| Mobile app + backend | **A: Expo + Hono backend** |
| Content site с SEO | **B: Next.js + Fastify** |
| Внутренний tool с тяжёлой ML-логикой | **C: Python + Supabase** |

## See also

- `stacks-lean-default.md` — Track A (Bun + Hono для non-SSR)
- `stacks-backend.md` — Track B (Node + Fastify enterprise)
- `stacks-frontend.md` — Frontend выбор (Next.js, Vite)
- `stacks-data-layer.md` — Supabase vs Yandex Cloud vs self-hosted
- `ai-llm.md` — RAG, vector DB, prompt observability
