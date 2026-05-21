---
name: workshop
description: EdgeLab online workshop — универсальный скилл для всего, что связано с воркшопом «Запусти AI-агента за 3 дня» на <your-workshop-domain>. Покрывает создание и редактирование лендинг-страниц дней, добавление видео-уроков через Kinescope, генерацию таймкодов через AssemblyAI, деплой на prod server, бренд дизайн-систему EdgeLab, RU+EN паритет, обратную связь user. Обязательно использовать при любом упоминании воркшопа, <your-workshop-domain>, online-workshop-edgelab, правки дня 0/1/2/3, добавления урока или видео, таймкодов эфира, Kinescope, деплоя воркшопа, даже если пользователь не назвал «скилл» явно. Триггеры — «воркшоп», «workshop», «<your-workshop-domain>», «добавь урок воркшопа», «новый урок дня», «залей видео на воркшоп», «таймкоды воркшопа», «новый день воркшопа», «редактирование воркшопа», «deploy workshop», «online-workshop-edgelab», «день 0/1/2/3», «эфир воркшопа», «Kinescope workshop». При ambiguous-запросах («добавь урок», «добавь курс», «новый модуль» без контекста) — сначала уточнить у пользователя: это воркшоп или клуб. НЕ использовать для контента платформы клуба (<your-platform-domain> / <your-staging-domain>, репо platform-edgelab + edgehub) — это отдельный продукт с курсами, профилями, лидербордом, EdgeHub-нетворкингом; воркшоп и клуб не путать.
---

# EdgeLab Workshop

Универсальный скилл for all agents, работающих с воркшопом «Запусти AI-агента за 3 дня» на `<your-workshop-domain>`. Любой агент читает этот файл + нужную справку из `references/` и может сделать задачу end-to-end — от правки копирайта до выкладки нового видео-урока с таймкодами.

## Когда использовать

- Правка или добавление контента на страницах `/day-N/`.
- Создание нового дня (полная новая страница с нуля).
- Обработка Zoom-записи эфира → Kinescope → таймкоды → встройка на страницу.
- Добавление skill-тестов, чек-листов, промптов для учеников.
- Изменение дизайна, цветов, компонентов (в рамках бренда).
- Деплой изменений на prod server prod (`/var/www/<your-workshop>`).
- Любая работа с репозиторием `<your-github-org>/<your-workshop-repo>`.

## Маршрутизация по задачам

Каждая под-задача описана в отдельном файле `references/`. Открывай только тот, который нужен прямо сейчас — это экономит контекст.

| Что нужно сделать | Читать файл |
|---|---|
| Понять где сайты, репо, пути, домены, кто за что отвечает | `references/01-architecture.md` |
| Узнать палитру, типографику, компоненты, бренд-токены | `references/02-design-system.md` |
| Создать новый день с нуля (лендинг-страница) | `references/03-create-landing.md` |
| Отредактировать существующий день (копия, блоки, бейджи) | `references/04-edit-landing.md` |
| Залить видео-урок на Kinescope и встроить на страницу | `references/05-add-lesson-video.md` |
| Сгенерировать таймкоды из записи эфира (AssemblyAI pipeline) | `references/06-timecodes.md` |
| Задеплоить изменения на prod server + проверка 200 | `references/07-deploy.md` |
| Антипаттерны, обратная связь user, грабли | `references/08-learnings.md` |

## Quick-start для нового агента

1. **Клонировать / обновить репо:**
   ```bash
   [ -d /tmp/online-workshop-edgelab ] \
     && (cd /tmp/online-workshop-edgelab && git pull) \
     || git clone git@github.com:<your-github-org>/<your-workshop-repo>.git /tmp/online-workshop-edgelab
   ```

2. **Правь RU:** `site/index.html`, `site/day-N/index.html`.

3. **Зеркаль EN:** `site/en/index.html`, `site/en/day-N/index.html`. Структура должна быть строка-в-строку — deploy-скрипт валидирует паритет по количеству строк.

4. **Деплой:**
   ```bash
   cd /tmp/online-workshop-edgelab && bash scripts/deploy.sh [day-0|day-1|day-2|day-3|day-all]
   ```
   Скрипт сам делает бэкап, rsync, проверку всех 10 страниц 200.

5. **Commit + push** в `main` (репо приватный, push автономно).

## Hard rules

- **Репо = source of truth. Прод = зеркало.** ВСЕ правки <your-workshop-domain> — ТОЛЬКО через репо `<your-github-org>/<your-workshop-repo>`: правка в `site/` (RU) и `site/en/` (EN) → commit + push в main → `scripts/deploy.sh`. НИКОГДА не редактировать `/var/www/<your-workshop>/` напрямую через ssh/scp/rsync/nano. Иначе следующий `deploy.sh` (от тебя или другого агента) снесёт твои правки — это реально случилось 2026-04-23: coordinator edited Day-3 прямо на проде, reviewer deployed через скрипт, изменения стерлись.
- **RU+EN паритет.** Если меняешь `site/day-N/index.html`, сразу меняй `site/en/day-N/index.html`. Иначе deploy провалится на check-only.
- **Бэкап до деплоя.** `scripts/deploy.sh` делает автоматически — не отключай.
- **Prod deploy — автономно.** Это НЕ <your-domain>/price (продажный лендинг, требует явного OK). Workshop — staging-like, деплой свободно.
- **Бренд-токены.** Не изобретать цвета. Палитра зафиксирована в `references/02-design-system.md`.
- **Kinescope**, не YouTube/Vimeo. Iframe-embed по стандартному паттерну (см. `05-add-lesson-video.md`).
- **AI-Native тесты.** Если ученику надо что-то проверить — давай ОДИН промпт для его Jarvis, а не список bash-команд. Агент сам продиагностирует и приложит источники.
- **Название `Jarvis` и `Richard` — это роли, не имена ботов ученика.** В промптах писать нейтрально («попроси основного агента»).

## Репозиторий и сервер

- **Canonical repo:** `github.com/<your-github-org>/<your-workshop-repo>` (приватный).
- **DEPRECATED:** `<your-github-org>/workshop-edgelab-su` — не трогать, там старая версия.
- **Prod:** prod server `<your-prod-server-ip>`, путь `/var/www/<your-workshop>`, Caddy с auto-TLS.
- **Домены:** `<your-workshop-domain>` (RU default) + `/en/` подпапка (EN).

## Workshop ≠ EdgeLab Club (hard rule — не путать)

В экосистеме EdgeLab два разных продукта. Контент в них НЕ пересекается — не переноси руками.

| Свойство | **Workshop** (этот скилл) | **Club / Platform** (отдельный продукт, скилла пока нет) |
|---|---|---|
| URL | `<your-workshop-domain>` | `<your-platform-domain>` (prod), `<your-staging-domain>` (staging) |
| Что это | Бесплатный онлайн-воркшоп: 4 дня (0-3), видео эфиров, таймкоды, гайды учеников | Платная платформа клуба EdgeLab: курсы, профили владельцев + агентов, лидерборд, EdgeHub-нетворкинг |
| Формат | Статический сайт: HTML + Tailwind CDN + лёгкий inline JS (копирование, UI-helpers) | Next.js 15 + Supabase (auth, storage, Postgres) |
| Репо | `<your-github-org>/<your-workshop-repo>` (этот) | `<your-github-org>/<your-platform-repo>` (frontend), `<your-github-org>/<your-edgehub-repo>` (нетворкинг агентов), backend на Thrall (`iel-launch-bot`) |
| Деплой | `scripts/deploy.sh` на prod server `/var/www/<your-workshop>/` | Отдельный pipeline (staging Thrall → prod prod server), другие пути |
| Доступ | Открытый, без логина | По оплате через `telegram-bot-edgelab`, тарифы Free/Edge/Pro/VIP |
| Контент живёт | В `site/day-N/index.html` как HTML-секции | В Supabase + React-компонентах (`platform-edgelab`) |
| Правит | Этот скилл (`workshop`) | Отдельный флоу (нет универсального скилла, работа через `platform-edgelab` README) |

**Сигналы что задача про Club, НЕ про воркшоп:**
- Упоминание `<your-platform-domain>`, `<your-staging-domain>`, EdgeHub, «клуб»
- Профили владельцев/агентов (`agent_name`, `agent_avatar`, `agent_bio`)
- Лидерборд, Supabase RLS, auth-flow, тарифы Edge/Pro/VIP
- «Курс внутри клуба», «урок в платформе», «новый раздел платформы»

**Сигналы что задача про Workshop (этот скилл):**
- Упоминание `<your-workshop-domain>`, «день 0/1/2/3», эфир, Kinescope embed
- Таймкоды, AssemblyAI, ffmpeg-конвертация
- Static-лендинг, RU+EN паритет, deploy.sh, `/var/www/<your-workshop>/`
- Бесплатный онлайн-курс «Запусти AI-агента за 3 дня»

Если сомневаешься — уточни у user «это воркшоп или клуб?» ПЕРЕД правкой. Правка не в тот репо = двойная работа на откат.

## Как этот скилл соотносится с другими

- **`edgelab-sale-landing`** (Thrall, shared) — бренд дизайн-система EdgeLab (цвета, типографика). Workshop использует ТЕ ЖЕ токены — обращайся туда за `references/design-system.md`, `tov.md`, `components.md`. Sales-лендинг `<your-domain>` (редиректит на воркшоп-оффер) — это тоже зона `edgelab-sale-landing`, не этого скилла.
- **`edgelab-workshop-zoom`** (в этом же репо, `skills/edgelab-workshop-zoom/`) — обработка Zoom-записи (скачать → AssemblyAI → Kinescope). Этот скилл переопределяет и дополняет workflow-zoom; при расхождениях — верить этому скиллу.
- **`forum-guides-authoring-portal`** — другой сайт (`<your-guides-domain>`, статьи-гайды), не путать.
- **Platform / EdgeHub** (`platform-edgelab`, `edgehub` репо) — клуб EdgeLab. Отдельный продукт, отдельный стек, отдельные правки. См. таблицу выше.

При любом конфликте с другими скиллами — этот (workshop) является источником правды для `<your-workshop-domain>`.
