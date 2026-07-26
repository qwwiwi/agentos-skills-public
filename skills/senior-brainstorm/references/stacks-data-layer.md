---
last_verified: 2026-05-11
applies_to: [early-stage, growth]
confidence: high
---

# Data Layer

Выбор слоя данных и BaaS для нового проекта. Покрывает: что входит в каждое решение, цены, lock-in, data residency (включая 152-ФЗ для РФ), типовые сценарии.

## Three main paths

| Path | Что это | Когда брать |
|---|---|---|
| **A. Managed BaaS** | Supabase / Firebase / Appwrite — Postgres + Auth + Storage + Realtime + Edge Functions в одном | MVP, маленькая команда, скорость старта важнее всего |
| **B. Cloud Postgres + your backend** | Neon / Supabase DB-only / DO Managed Postgres + ваш Hono/FastAPI/Fastify | Когда BaaS-функции лишние, нужен полный контроль над API |
| **C. Russian cloud** | Yandex Cloud / SberCloud / VK Cloud (Managed Postgres + Functions + Object Storage) | 152-ФЗ residency, российская юрлица, требование локализации ПД |

## Path A — Managed BaaS (Supabase deep-dive)

Supabase даёт «Firebase на Postgres»: всё в одном API, scale-out до production уровня.

**Что входит:**

- **Postgres** (managed, любая extension) — основная БД
- **Auth** — magic link, OAuth (Google/GitHub/Apple/...), MFA, anonymous, organizations
- **Realtime** — WebSocket с подпиской на row-level изменения, presence, broadcast
- **Storage** — S3-совместимое хранилище файлов + image transforms
- **Edge Functions** — Deno-серверless, низкая холодная задержка, deploy одной командой
- **Vector** — `pgvector` встроен, эмбеддинги/семантический поиск без отдельной БД

**Цены** (на 2026-05):

| Tier | Цена | Включено |
|---|---|---|
| Free | $0 | 500MB БД, 1GB Storage, 50k MAU, 500k Edge invocations |
| Pro | $25/мес | 8GB БД, 100GB Storage, 100k MAU, 2M invocations |
| Team | $599/мес | SLA, SOC 2, точка-в-времени восстановление 7 дней |

**Pros:**

- От нуля до auth+DB+storage за час
- Row Level Security (RLS) — мощная авторизация на уровне строк
- Edge Functions ставят на Cloudflare-сеть, низкая latency глобально
- Open-source self-hosting опция (вы можете уйти)

**Cons:**

- Realtime на heavy workload требует тюнинга (connection limits)
- Edge Functions на Deno — отдельная экосистема от вашего backend
- Vendor lock-in на Auth/RLS пакеты, миграция требует усилий
- Цена резко растёт после Pro (Team $599)

**Когда брать:** MVP, бот с БД, веб-приложение с auth, в команде 1-3 разработчика, нужна скорость.

**Когда не брать:** требуется кастомная business-логика в БД, сложные транзакции, > 1000 RPS на запись без horizontal scaling.

## Path B — Cloud Postgres + your backend

Когда BaaS-абстракции мешают, и хочется control: только managed БД + ваш API сверху.

**Provider options:**

| Provider | Plus | Minus |
|---|---|---|
| Neon | Serverless Postgres, branching для preview-окружений, scale-to-zero | Меньше регионов чем Supabase |
| Supabase (DB-only) | Те же managed-возможности, но без Auth/Storage | Платите за Pro даже если используете только БД |
| DigitalOcean Managed Postgres | Простой UI, понятные цены | Меньше features (нет branching) |
| AWS RDS | Enterprise-grade, любая extension | Дорого, операционная сложность |

**Backend pairs:**

- Bun + Hono + Drizzle/Prisma (см. `stacks-lean-default.md`)
- Node + Fastify + Prisma (см. `stacks-backend.md` Track B)
- Python + FastAPI + SQLAlchemy/asyncpg (см. `stacks-python-supabase.md`)

**Pros:**

- Полный контроль над API дизайном
- Можно делать сложные миграции, partitioning, custom extensions
- Лёгкая миграция между cloud-провайдерами (Postgres везде Postgres)

**Cons:**

- Auth/Storage/Realtime пишите сами (или берёте Auth0/Clerk/Better Auth отдельно)
- Operations overhead — pgbouncer, backups, мониторинг

**Когда брать:** есть expertise, нужны кастомные features, объём > 100GB БД, > 100 RPS.

## Path C — Russian cloud (Yandex Cloud / SberCloud / VK Cloud)

Только при жёстком требовании 152-ФЗ residency или работе с российскими гос-заказами. Иначе оверкилл.

**Yandex Cloud (наиболее зрелый):**

- **Managed Service for PostgreSQL** — Postgres 16, авто-бэкапы, репликация
- **Cloud Functions** — serverless (Node, Python, Go), холодный старт 100-300ms
- **Object Storage** — S3-совместимое
- **Serverless Containers** — Docker-контейнеры в serverless mode (для FastAPI, Hono, etc.)
- **Managed Kubernetes** — если нужен оркестратор

**Pros:**

- 152-ФЗ compliance из коробки (договор по обработке ПД, hosting в РФ)
- Цены в рублях, оплата с российских счетов
- SLA подписан в РФ юрисдикции

**Cons:**

- Меньше features чем AWS/GCP
- Документация на русском и английском, но иногда отстаёт от изменений
- Community меньше — баги Stack Overflow ищите дольше
- Edge Functions (как у Supabase Edge / Cloudflare Workers) — нет аналога

**Альтернативы Yandex:** SberCloud (госсектор), VK Cloud (молодой), Selectel (VPS + managed services).

## Decision matrix

| Сценарий | Recommended |
|---|---|
| MVP, 1 разработчик, нужно за неделю | **A: Supabase** |
| Бот + БД, маленькая команда | **A: Supabase** |
| Веб-приложение с auth, до 10k MAU | **A: Supabase Pro** |
| Контентная платформа с CDN | **A: Supabase + Cloudflare** |
| Кастомный API + сложная логика | **B: Neon + Hono/FastAPI** |
| Enterprise SaaS с SSO | **B: AWS RDS + Auth0 + your backend** |
| 152-ФЗ residency обязательно | **C: Yandex Cloud Managed PG + Serverless Containers** |
| Госзаказ РФ | **C: SberCloud / Selectel + on-prem** |

## API patterns — как фронтенд достаёт данные

После выбора слоя данных встаёт вопрос «как фронтенд их получает». Три типовых паттерна:

| Pattern | Реализация | Когда |
|---|---|---|
| **Direct from BaaS** | Supabase JS клиент в браузере, RLS защищает данные | MVP, нет сложной серверной логики |
| **API gateway** | Frontend → ваш backend (FastAPI/Hono) → БД | Нужна серверная валидация, бизнес-логика, агрегации |
| **Hybrid** | Read через BaaS клиент, write через API | Большая часть — read-only, мутации требуют логики |

**Direct-from-BaaS — главное правило:** работает только при правильно настроенном RLS. Без RLS = открытая БД в публичный интернет. Перед запуском пройдите [Supabase RLS checklist](https://supabase.com/docs/guides/database/postgres/row-level-security).

## Edge Functions vs Containers vs Always-on backend

Три способа запускать серверный код:

| Option | Latency | Холодный старт | Когда |
|---|---|---|---|
| **Edge Functions** (Supabase Edge, Cloudflare Workers, Yandex Functions) | Глобально низкая | 50-300ms | Простые webhooks, image transforms, redirects |
| **Serverless Containers** (Yandex Serverless Containers, AWS Lambda + Docker, GCP Cloud Run) | Регион-зависима | 200-2000ms | Тяжёлые операции, ML inference, специфичные runtime |
| **Always-on VPS / VM** (Timeweb / DigitalOcean / Hetzner) | Зависит от региона | 0ms | Боты с long-polling, WebSocket-сервера, продолжительные процессы |

**Правило большого пальца:** холодный старт > 500ms ломает UX. Если функция вызывается на каждый клик пользователя — нужен always-on или edge. Если раз в час webhook — serverless норм.

## Migration paths

Что если выбрал не то и хочется уйти:

- **Supabase → self-hosted Postgres:** `pg_dump`/`pg_restore`, Auth и Storage переносите отдельно (Auth0 + S3). Realtime придётся переписать (например, на Centrifugo).
- **Yandex Cloud → AWS/GCP:** Postgres переезжает чисто. Functions переписать (Node→Lambda).
- **Firebase → Supabase:** структура Firestore (документы) → Postgres (таблицы) — это переписать схему. Auth переезжает через export users CSV.

## Pre-launch checklist (data layer)

- [ ] Backup policy: автоматические бэкапы + точка-в-времени восстановление до 7 дней
- [ ] Connection pooling: pgBouncer / Supabase pooler настроен под ожидаемую нагрузку
- [ ] RLS policy: row-level security включён на всех таблицах с user-data
- [ ] Secrets rotation: пароли БД ротируются автоматически (по возможности)
- [ ] Monitoring: алерт на > 80% disk, > 80% connections, slow queries > 1s
- [ ] Data residency: если EU/RU users — проверены legal требования (GDPR, 152-ФЗ)

## See also

- `stacks-lean-default.md` — opinionated default for non-SSR с Bun + Hono
- `stacks-python-supabase.md` — Python + FastAPI + Supabase трек
- `stacks-backend.md` — Node + Fastify enterprise трек
- `security.md` — threat modeling для data layer (RLS, secrets, breach response)
