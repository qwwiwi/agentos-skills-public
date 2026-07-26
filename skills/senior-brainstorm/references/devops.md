---
last_verified: 2026-04-15
applies_to: [early-stage, growth, scale]
confidence: high
---

# DevOps & Observability

## Deployment Ladder (stage-aware)

| Стадия | Инфра | Почему |
|--------|-------|--------|
| MVP / early-stage | Vercel / Render / Fly.io | Zero ops, быстрый деплой, бесплатный tier |
| Growth (10K+ users) | AWS ECS / Fargate, managed DB | Контроль, масштабирование, cost control |
| Scale (100K+ users) | Kubernetes (EKS/GKE) | Оркестрация, auto-scaling, service mesh |

**Default: НЕ начинать с K8s.** K8s только при явных требованиях к масштабу или multi-service architecture.

## Containerization

- **Docker** -- контейнеризация, multi-stage builds, slim images
- **Docker Compose** -- локальная разработка (app + DB + Redis + queue)
- Kubernetes -- только на стадии Scale (см. ladder выше)

## CI/CD Pipeline

- GitHub Actions (или GitLab CI)
- Stages: lint -> test -> build -> scan -> deploy staging -> E2E -> deploy prod
- Feature flags (LaunchDarkly / Unleash) для progressive rollout
- Rollback procedure: одна команда, < 5 минут

## Release Strategy

| Стратегия | Когда |
|-----------|-------|
| Rolling deploy | Default для большинства SaaS |
| Blue-green | Нужен instant rollback |
| Canary | High-traffic, нужна осторожность |
| Feature flags | Деплой кода без активации фичи |

## Environments

- **Local**: Docker Compose (полная копия стека)
- **Preview**: Vercel preview per PR (с E2E smoke тестами)
- **Staging**: зеркало production, seed data
- **Production**: managed, мониторинг, алерты

## Observability (OpenTelemetry-first)

- **OpenTelemetry** -- единый стандарт для traces, metrics, logs
- **Prometheus** -- метрики (custom + infra)
- **Grafana** -- визуализация дашбордов
- **Loki** -- агрегация логов (structured JSON logs)
- **Tempo** -- distributed tracing (correlation IDs, span propagation)
- **Sentry** -- ошибки в реальном времени, release tracking

## SLO / Alerting

- SLI: availability (99.9%), latency p95 < 500ms, error rate < 0.1%
- Error budgets: burn rate alerts
- Alert routing: PagerDuty / Opsgenie -> on-call
- Runbooks для top-5 инцидентов

## Cost Governance

- CDN egress monitoring
- Video storage lifecycle (hot -> warm -> cold)
- Preview environment auto-cleanup (TTL)
- Spot instances для CI runners

## Backup & DR

- Automated daily backups + WAL archiving
- RPO < 1 час, RTO < 4 часа (для SaaS)
- Restore drills: ежеквартальный тест восстановления
- Multi-region для enterprise tier
