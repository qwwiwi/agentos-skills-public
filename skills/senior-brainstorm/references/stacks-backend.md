---
last_verified: 2026-04-15
applies_to: [early-stage, growth, scale]
confidence: high
---

# Backend

> **Three tracks. Pick by team strength and project type:**
>
> - **Track A — Bun + Hono** — `stacks-lean-default.md`. Default для non-SSR (SPA, mobile, desktop, internal API, bot backend).
> - **Track B — Node + Fastify** — this document. Для EdTech SaaS, Stripe ecosystem, enterprise auth, Next.js API routes
> - **Track C — Python + FastAPI** — `stacks-python-supabase.md`. Для Telegram-ботов, AI/ML, data-heavy сценариев, команд сильных в Python

## When to use this (Node + Fastify) track

- EdTech SaaS with Stripe Billing + Connect
- BullMQ job queues with Redis
- Enterprise auth (Clerk, Auth0, SSO/SAML)
- Multi-tenancy with Postgres RLS at scale
- Next.js API routes as the web backend

## When to use Lean track instead

- Small service, SPA backend, internal tool
- Want TypeScript runtime without build step (Bun)
- Prefer Hono minimal framework (~2KB) over Fastify
- No mature Node ecosystem needed

## Core Stack

- **Node.js 22 LTS** (или актуальный LTS для стабильности)
- **Fastify 5** (или Express для простоты)
- **PostgreSQL 18** (или managed -- Supabase, Neon, RDS)
- **Redis** -- кэш, сессии, очереди (BullMQ)

## ORM / Data Access

| Инструмент | Когда | Tradeoff |
|------------|-------|----------|
| Prisma 6+ | Команда < 5, rapid development, type safety | Тяжелее, сложные запросы неудобны |
| Drizzle ORM | SQL-first, легкий, performance-critical | Меньше экосистема, больше ручной работы |
| Raw SQL / Kysely | Сложные аналитические запросы, миграции | Нет type safety из коробки |

## API Strategy

| Подход | Когда | Tradeoff |
|--------|-------|----------|
| REST | Default для большинства SaaS | Overfetching, версионирование |
| tRPC | Fullstack TS, один репо, маленькая команда | Привязка к TypeScript |
| GraphQL | Разные клиенты (web + mobile + API) | Сложность, N+1, security |

## Auth Provider

| Провайдер | Когда | Tradeoff |
|-----------|-------|----------|
| Clerk | Быстрый старт, Organizations из коробки | Vendor lock-in, цена на масштабе |
| Auth0 | Enterprise SSO (SAML, SCIM), B2B | Сложная настройка, дорого |
| Auth.js (NextAuth v5) | Полный контроль, self-hosted | Нет MFA, Organizations, passkeys из коробки |
| Better Auth | Open-source, плагины (2FA, organizations) | Молодой проект, меньше community |

## Auth & Authorization

- RBAC для базовых ролей (student, instructor, admin)
- ABAC поверх RBAC когда нужна логика владения ("инструктор редактирует только свои курсы")
- Tenant scoping + feature entitlements для B2B

## Payments

- **Stripe 17+** (Billing, Connect для маркетплейса инструкторов)
- Webhook idempotency: event_id + unique index + dedup check
- Stripe Test Clocks для тестирования lifecycle
- PCI DSS: offload на Stripe (SAQ A) -- никогда не хранить карты

## Background Jobs

- **BullMQ** (Redis) -- drip content, email, webhooks
- Idempotency keys на каждый job
- DLQ (Dead Letter Queue) для failed jobs
- Retry с exponential backoff
- Scheduling: cron jobs через BullMQ repeatable

## Domain Model (EdTech)

```
Organization (school/tenant)
  |-- Instructor (creator of courses)
  |-- Student (enrolled learner)
  |-- Course
  |     |-- Module
  |     |     |-- Lesson (video, text, quiz)
  |     |-- Enrollment (student -> course, status, progress)
  |     |-- Certificate (on completion)
  |-- Cohort (group of students, schedule)
  |-- Subscription (billing plan)
  |-- Entitlement (what access a subscription grants)
```

## Multi-tenancy

| Подход | Когда | Tradeoff |
|--------|-------|----------|
| Shared DB + RLS | Default для SaaS. PostgreSQL RLS | Сложнее миграции, один сбой -- все tenant'ы |
| Schema-per-tenant | Enterprise, strict isolation | Дорого, сложно мигрировать |
| DB-per-tenant | Compliance, физическая изоляция | Очень дорого, сложные операции |

## DB Operations

- Connection pooling: PgBouncer или Supabase pooler
- Read replicas для аналитики
- Migration strategy: `prisma migrate` / `drizzle-kit` + zero-downtime migrations
- Backup: daily automated + WAL archiving
