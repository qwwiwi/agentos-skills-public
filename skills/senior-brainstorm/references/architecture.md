---
last_verified: 2026-04-15
applies_to: [early-stage, growth, scale]
confidence: high
---

# Architecture

## Architecture Progression (stage-aware)

```
Stage 1: Modular Monolith (DEFAULT)
  |-- Single Next.js app
  |-- PostgreSQL + Redis
  |-- Clear module boundaries (billing, courses, auth, media)
  |-- Deploy: Vercel / single container
  |
Stage 2: Extract on Pressure
  |-- Media processing -> отдельный сервис (video encoding, CDN)
  |-- Background jobs -> отдельный worker
  |-- Analytics -> read replica + CQRS
  |
Stage 3: Services (только при доказанной необходимости)
  |-- Event-driven communication (SQS/SNS, NOT Kafka for most SaaS)
  |-- Service mesh (Istio / Linkerd)
  |-- Per-service DB
```

**Default: модульный монолит.** Микросервисы -- только при доказанной нагрузке или организационной необходимости (>3 команд).

## Паттерны с трейдоффами

| Паттерн | Когда применять | Когда НЕ применять | Cognitive load |
|---------|----------------|-------------------|----------------|
| Modular Monolith | Default для SaaS, команда < 10 | Никогда не рано | Low |
| DDD | Сложный домен (>5 bounded contexts) | CRUD-приложения, MVP | High |
| Event-Driven | Асинхронные workflows, decoupling | Синхронные CRUD, команда < 3 | High |
| CQRS | Разные модели чтения/записи (аналитика) | Простые queries, early-stage | Medium |
| Serverless | Spike-нагрузки, event processing | Steady-state workloads, long-running | Medium |

## Bounded Contexts (EdTech)

```
Identity (auth, profiles, organizations)
  |
Catalog (courses, modules, lessons, content)
  |
Enrollment (subscriptions, access, entitlements)
  |
Progress (completion, certificates, achievements)
  |
Billing (payments, invoices, refunds)
  |
Media (video upload, encoding, streaming, CDN)
  |
Analytics (events, funnels, reports)
  |
Notifications (email, push, in-app)
```

## Infrastructure

| Компонент | Early-stage | Growth | Scale |
|-----------|------------|--------|-------|
| Compute | Vercel / Fly.io | AWS ECS Fargate | EKS / GKE |
| CDN | Cloudflare (free) | Cloudflare Pro | Cloudflare Enterprise |
| Video | Mux / Kinescope | Mux + CDN | Custom pipeline + CDN |
| Storage | Supabase Storage | S3 / R2 | S3 + lifecycle policies |
| IaC | -- | Terraform | Terraform + Atlantis |

## ADR Template (Architecture Decision Record)

```markdown
# ADR-001: [Название решения]

## Контекст
[Какая проблема решается]

## Рассмотренные варианты
1. [Вариант A] -- [плюсы/минусы]
2. [Вариант B] -- [плюсы/минусы]
3. [Вариант C] -- [плюсы/минусы]

## Решение
[Что выбрали и почему]

## Последствия
[Что это означает для кодовой базы, инфры, команды]

## Статус
Proposed / Accepted / Deprecated
```
