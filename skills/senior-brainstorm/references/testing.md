---
last_verified: 2026-04-15
applies_to: [early-stage, growth, scale]
confidence: high
---

# Testing

## Strategy: Testing Trophy (адаптированная)

| Слой | Доля | Инструмент | Что тестировать |
|------|------|-----------|-----------------|
| Static | -- | TypeScript, ESLint | Типы, линтинг |
| Unit | 20% | Vitest | Чистая бизнес-логика, utils, helpers |
| Integration | 50% | Vitest + Testcontainers | API endpoints, DB queries, auth flows, webhooks |
| E2E | 20% | Playwright | Critical user journeys (enrollment, payment, video) |
| Contract | 10% | Pact | API контракты между сервисами |

**Anti-patterns:**

- НЕ тестировать UI-рендеринг на E2E уровне (snapshot hell)
- НЕ мокировать DB в integration тестах (Testcontainers дешевле)
- НЕ гнаться за 100% coverage (80%+ бизнес-логика, 60-70% общий)

## Unit Testing

- **Vitest** -- замена Jest (нативная ESM поддержка, быстрый startup)
- **React Testing Library** -- компоненты (user behavior, не implementation)
- **MSW v2** -- API mocking (Mock Service Worker)
- Async Server Components: unit-тесты ограничены, E2E через Playwright

## Integration Testing

- **Testcontainers** (`@testcontainers/postgresql`) -- реальный PostgreSQL в Docker
- **Transaction rollback pattern** -- seed once, rollback per test (98% быстрее)
- **Supertest** -- API endpoints

## E2E Testing

- **Playwright** -- multi-browser, parallelism, TypeScript-first
- Visual regression: `toHaveScreenshot()` (built-in)
- Mobile emulation: `devices['iPhone 14']`
- `storageState` -- auth reuse между тестами

## Performance Testing

- **k6 v1.0** -- load testing в CI (thresholds: p95 < 500ms)
- **Lighthouse CI** -- Core Web Vitals на ключевых страницах
- Bundle monitoring: `bundlewatch`

## Test Matrix по рискам (EdTech)

| Что тестировать | Слой | Как |
|----------------|------|-----|
| Enrollment flow | E2E | Playwright: регистрация -> оплата -> доступ |
| Payment lifecycle | Integration | Stripe Test Clocks: trial, renewal, failed payment |
| Webhook idempotency | Integration | Один event_id дважды, assert обработан 1 раз |
| Video streaming (HLS) | Integration | Валидация манифеста, Content-Type, signed URLs |
| User progress | Integration | Создание/обновление записей, идемпотентность |
| RLS isolation | Integration/DB | pgTAP: Tenant A не видит данные Tenant B |
| Permission leaks | Integration | Auth as different roles, assert access boundaries |
| Data migration | Integration | Apply migration, verify data integrity, rollback |

## CI/CD для тестов

- **Playwright sharding**: `--shard=1/4` + GitHub Actions matrix
- **Vitest sharding**: `--shard=1/4`
- `fullyParallel: true`
- Preview deploys: Vercel preview + Playwright smoke suite
- Flaky tests: `retries: 2` + `@flaky` tag + separate job
- Reporting: JUnit XML + GitHub annotations

## Failure-path Testing

- Stripe outage simulation
- Webhook duplication handling
- Queue poison messages (DLQ routing)
- Expired signed URLs
- DB connection failures (circuit breaker)
