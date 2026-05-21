# 01 — Архитектура: сайты, репо, серверы

Всё что нужно знать о физической инфраструктуре воркшопа перед любой работой.

## Репозитории

| Репо | Роль | Статус |
|---|---|---|
| `github.com/<your-github-org>/<your-workshop-repo>` | **Canonical.** Единственный источник правды. | active, private |
| `github.com/<your-github-org>/workshop-edgelab-su` | Старая версия. | **DEPRECATED** (есть `DEPRECATED.md`) |

Всегда работать с `online-workshop-edgelab`. В старый репо коммиты не пушить.

## Структура репо

```
online-workshop-edgelab/
├── README.md                 ← расписание, структура, ссылки
├── scripts/
│   └── deploy.sh             ← деплой + verify (единственный способ)
├── site/                     ← то, что деплоится на прод
│   ├── index.html            ← RU главная
│   ├── day-0/index.html      ← RU день 0 (подготовка)
│   ├── day-1/index.html      ← RU день 1 (База)
│   ├── day-2/index.html      ← RU день 2 (Авторский метод)
│   ├── day-3/index.html      ← RU день 3 (Скиллы)
│   └── en/
│       ├── index.html        ← EN главная
│       ├── day-0/index.html
│       ├── day-1/index.html
│       ├── day-2/index.html
│       └── day-3/index.html
├── day-0-preparation/        ← черновики/сценарий дня 0 (markdown)
├── day-1-base/               ← черновики дня 1
├── day-2-setup/              ← черновики дня 2
├── day-3-skills/             ← черновики дня 3
├── templates/                ← шаблоны CLAUDE.md, skills, конфиги для раздачи ученикам
├── assets/                   ← медиа, презентации
└── skills/
    ├── workshop/             ← этот скилл (универсальный)
    └── edgelab-workshop-zoom/ ← обработка Zoom-записей (под-скилл)
```

**Что деплоится:** только содержимое `site/` через rsync.
**Что НЕ деплоится:** `day-N-*/`, `templates/`, `assets/`, `skills/`, `README.md` — это внутренняя кухня.

## Домены и DNS

| Домен | Куда ведёт | Примечание |
|---|---|---|
| `<your-workshop-domain>` | prod server `<your-prod-server-ip>` | A-record, Caddy с auto-TLS |
| `<your-workshop-domain>/en/` | тот же VPS | отдельная подпапка в `site/en/` |

## Production server

| Параметр | Значение |
|---|---|
| SSH | `ssh root@<your-prod-server-ip>` |
| Путь | `/var/www/<your-workshop>/` |
| Web-сервер | Caddy (автоматический TLS через Let's Encrypt) |
| Процесс | статика, без PM2/Node — только rsync файлов |
| Backup | restic daily на DO Spaces (`<your-backup-bucket>` bucket, fra1) |

## Deploy target map

| Цель | Что обновится |
|---|---|
| `day-0` | RU+EN главная + `/day-0/` |
| `day-1` | `/day-1/` RU+EN (главная не трогается) |
| `day-2` | `/day-2/` RU+EN |
| `day-3` | `/day-3/` RU+EN |
| `day-all` | всё: главная + все 4 дня, RU+EN |

## Кто что трогает

| Агент | Роль на воркшопе |
|---|---|
| **coordinator** (Mac mini) | координатор, правит лендинги, генерирует таймкоды, деплоит |
| **content agent** (Mac mini) | контент — копирайт для промо-постов и pre-live материалов |
| **Thrall** (VPS) | архитектура, ревью, но НЕ пушит в workshop без задачи |
| **monitoring agent** (VPS) | monitoring, не трогает deploy |

## Связанные сервисы (и что к воркшопу НЕ относится)

Полная карта доменов EdgeLab — чтобы не перепутать, куда деплоить.

| Домен | Что это | Чей скилл |
|---|---|---|
| `<your-workshop-domain>` | **Воркшоп (этот)** — бесплатный онлайн-курс, 4 дня, static HTML | `workshop` (этот скилл) |
| `<your-domain>` | Sales-лендинг бренда (сейчас редирект на воркшоп-оффер) | `edgelab-sale-landing` (Thrall, shared) |
| `<your-domain>/price` | Страница тарифов клуба Edge/Pro/VIP | `edgelab-sale-landing` |
| `<your-domain>/install` | One-line installer для учеников (`edgelab-install` репо) | отдельная работа, не скилл |
| `<your-platform-domain>` | **Платформа клуба EdgeLab (production)** — Next.js + Supabase, курсы, профили, лидерборд | `platform-edgelab` репо (нет универсального скилла — работа через README репо) |
| `<your-staging-domain>` | **Платформа клуба (staging)** — тот же стек, staging VPS | `platform-edgelab` |
| `<your-guides-domain>` | Статьи-гайды (`guides-edgelab` репо) | `forum-guides-authoring-portal` |
| Telegram-каналы воркшопа | Промо, анонсы, live-стримы | content agent |

**Критичное разграничение workshop vs платформа клуба:**

- **Workshop** = статический сайт, контент лежит в `site/day-N/index.html` как HTML-секции. Бесплатный, без логина.
- **Платформа клуба** (`<your-platform-domain>`) = Next.js-приложение на Supabase. Курсы, уроки, профили владельцев и агентов, EdgeHub-нетворкинг. Доступ по оплате через `telegram-bot-edgelab` (тарифы Free/Edge/Pro/VIP).

Контент одного продукта НЕ переносить в другой руками. Если user говорит «добавь урок» — уточни, это урок на воркшопе (тогда правка `site/day-N/index.html`) или курс внутри клуба (правка `platform-edgelab` репо, не этот скилл). См. таблицу сигналов в `SKILL.md` секция «Workshop ≠ EdgeLab Club».

## Проверка доступа (для нового агента)

```bash
# Репо
git ls-remote git@github.com:<your-github-org>/<your-workshop-repo>.git HEAD

# Prod SSH
ssh root@<your-prod-server-ip> "ls /var/www/<your-workshop>/ | head"

# Live site
curl -sS -o /dev/null -w "%{http_code}\n" https://<your-workshop-domain>/
```

Если один из трёх падает — проблема с доступом, эскалировать к user.
