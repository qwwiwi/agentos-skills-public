---
name: agentos-content
description: >
  How to author, ship, and update content (lessons, bonuses) for the AgentOS intensive platform
  (<your-agentos-domain>). Covers source-of-truth pattern, mock layer, Supabase DB layer,
  block types, frontend rendering rules, deploy pipeline (build → tarball → prod server → PM2),
  and known pitfalls. Use when adding a new bonus, rewriting an existing lesson, changing
  block types, or shipping content updates to prod.
  Triggers: "добавь урок", "новый бонус", "обнови контент", "update lesson", "add bonus",
  "lesson 10 / 11 / 12", "intensive-agentos-platform", "<your-agentos-domain> content",
  "patch_db", "lessonN_steps".
  NOT for: backend logic changes, auth flows, payment integration, infrastructure work
  outside the content pipeline.
---

# AgentOS Content Pipeline

Authoritative guide for writing and shipping lessons / bonuses on `<your-agentos-domain>`.
Read this before touching anything in `apps/web/app/intensive/lesson/[id]/page.tsx` or
the `intensive_bonuses` Supabase table.

## When to use

- Adding a new bonus (текстовый гайд, без видео)
- Rewriting an existing lesson (e.g., changing structure, adding steps)
- Updating prompts / repos / outcome / skills inside an existing bonus
- Shipping any content change to production

## Не использовать для

- Изменений auth / payments / API endpoints (это отдельный стек)
- Бекенд миграций (Supabase schema changes — отдельный workflow)
- Изменений рендерера блоков (`UnifiedBlockRenderer.tsx`) без понимания всех уроков

## Workflow at a glance

```
1. Author Python source-of-truth file       → /tmp/lessonN_steps.py
2. Generate TS mock from source             → python3 /tmp/update_mock_lN.py
3. Patch Supabase DB from same source       → ssh thrall + python3 patch_db_lN.py
4. Build Next.js standalone                 → npm run build
5. Stage tarball + scp to prod server           → /tmp/web-stage-vN/ → /tmp/web-deploy.tgz
6. Unpack on prod + PM2 restart             → cd /var/www/<your-project> && tar -xzf
7. Verify HTTP 200 + visible content        → curl https://<your-agentos-domain>/intensive/lesson/N
8. **Visual verify (MANDATORY)**            → agent-browser → screenshot mobile → проверить глазами
9. Commit + push                            → <your-github-org>/<your-platform-repo> main
```

## Critical rules (read before any change)

1. **Source-of-truth is Python**, not TS or JSON. One Python file drives both mock and DB —
   so they NEVER diverge. See `references/02-source-of-truth.md`.

2. **`re.sub` replacement strings interpret `\\n` as newline.** This will silently break
   your generated TypeScript with «Unterminated string constant». Always wrap repl in
   `lambda m: repl_str`. See `references/06-pitfalls.md` Pitfall #1.

3. **Stale `/tmp/lessonN_steps.py` on Thrall.** `patch_db.py` does
   `sys.path.insert(0, '/tmp')`. If an old version sits in `/tmp` (from a previous session),
   it will load that one instead of yours and silently patch the WRONG content. Always
   `cp /root/lessonN_steps.py /tmp/lessonN_steps.py` before running patch_db. See
   Pitfall #2.

4. **Bonus pages don't show video or timecodes.** `bonusN !== null` in
   `apps/web/app/intensive/lesson/[id]/page.tsx` controls this. Don't accidentally
   re-enable them.

5. **No ID buttons on any block.** Earlier ID copy was visual noise — removed from
   step / code / prompt / mcp_config / agent_config. Only main «Копировать» (content)
   button remains.

6. **Production deploy goes to prod server (<your-prod-server-ip>)**, NOT Thrall. DNS for
   `<your-agentos-domain>` points at prod server. There IS a shadow PM2 `<your-pm2-name>`
   on Thrall :3020 — deploying there looks green on internal curl but prince sees old
   code. Always `dig +short <your-agentos-domain>` before deploy.

7. **Service-role-key NEVER in chat output.** `bot/.env` on Thrall contains
   SUPABASE_SERVICE_ROLE_KEY which bypasses RLS. Never `cat bot/.env`, never
   `tr "\0" "\n" < /proc/PID/environ` without `| grep -v ROLE_KEY`. See Pitfall #5.

8. **Visual verify after deploy is MANDATORY (HARD RULE).** После любого
   UI-deploy НЕЛЬЗЯ рапортовать «Готово» только на основе HTTP 200 + grep
   на ключевые строки. `grep` ловит **наличие** нужного, но не **отсутствие**
   лишних элементов от прошлой версии. Обязательный шаг:
   - открыть страницу через `agent-browser` (CDP, headless Chrome)
   - mobile viewport (375px width)
   - screenshot full-page (проскроллить полностью включая footer)
   - глазами сверить с ожиданием: positive (новое есть) + negative (старого нет)
   - только потом «Готово»

   Если visual verify не сделана (agent-browser недоступен) — явно сказать
   user: «визуально не проверила, могут быть остаточные UI-элементы».
   См. Pitfall #9 в `references/06-pitfalls.md`. Применяется ко ВСЕМ
   UI-задачам: EdgeLab, AgentOS Intensive, workshop, любая страница на
   `*.<your-domain>`.

10. **READ README перед build/deploy (HARD RULE, 2026-05-13).** Перед `npm run build`
    либо правкой env / deploy скриптов / infra — обязательно `Read README.md` репо
    целиком (или `Grep` по «deploy», «env», «host», «prod», «production»). Не доверяй
    `.env.example` (часто staging-значения) и устаревшим skill-файлам. README на HEAD —
    canonical. Эту ошибку уже один раз получили (NEXT_PUBLIC_API_BASE_URL из staging
    значения сломал prod). См. Pitfall #11 + `core/rules.md` главное правило.

11. **«Материалы» эфира = поле `materials`, не `blocks` (HARD RULE).** На странице эфира
    вкладка-счётчик «Материалы · N» считает из `intensive_eth_details.materials` (массив
    `{name, desc, url, filename}`), НЕ из link-блоков внутри `blocks`. После добавления
    link-блоков в описание шага обязательно параллельно PATCH `materials` тем же набором.
    См. Pitfall #15.

12. **Cabinet счётчики материалов — хардкод-мок (HARD RULE).** `apps/web/app/intensive/cabinet/page.tsx`
    имеет массив `BROADCASTS` с полями `materials`/`lessons`/`open` зашитыми статикой.
    Ничего не читает из БД. При добавлении материалов к эфиру N — параллельно
    править `BROADCASTS[N-1].materials` и делать полный rebuild + redeploy. См. Pitfall #16.

13. **Hot-patch скомпилированных chunks с тем же hash — антипаттерн (HARD RULE).**
    Браузер кеширует chunk по hash в имени файла как immutable. Правка содержимого
    без смены hash → у существующих посетителей старый код, у новых — новый. Всегда
    полный `npm run build` (получит новый hash) → tarball → scp → `pm2 restart`.
    См. Pitfall #12.

14. **Статика только вне `/intensive/*` префикса.** Next.js app router имеет роуты
    `/intensive/cabinet`, `/intensive/eth/[id]`, `/intensive/lesson/[id]` и т.д. Файлы
    в `public/intensive/<anything>/...` → HTTP 404 из-за конфликта. Паттерн в проекте:
    `public/efir-N/...` → `/efir-N/...`. После добавления статики в public/ —
    обязательный `pm2 restart` (Next.js standalone кеширует listing при старте,
    см. Pitfall #14).

9. **Контент урока живёт в 4 местах, не в одном (HARD RULE).** После любого
   изменения контента урока обязательно обновить ВСЕ 4 источника, иначе
   listing-страницы покажут старое:
   - DB `intensive_lessons.blocks` — детальная страница
   - `BONUS_LESSONS` / `ONBOARDING_LESSONS` mock в `app/intensive/lesson/[id]/page.tsx` — SSR fallback
   - `LESSONS[]` hardcoded в `app/intensive/cabinet/onboarding/page.tsx` — список предобучения
   - `FEED_ITEMS[]` hardcoded в `app/intensive/materials/page.tsx` — агрегация материалов

   Обязательный grep-чеклист после изменения:
   ```bash
   grep -rn "ONBOARDING_LESSONS\|BONUS_LESSONS\|FEED_ITEMS\|LESSONS\[" apps/web/app/
   ```
   Visual verify (#8) ловит автоматически — если делать скриншот
   listing-страниц, а не только детальной. См. Pitfall #10.

## Detailed references

Open ONLY the reference you need (don't load all on every task):

- `references/01-architecture.md` — bonus vs lesson, ID mapping (lesson 10 ↔ bonus 1),
  full block-types table, where each piece of content lives.
- `references/02-source-of-truth.md` — Python source file structure, helper conventions,
  step / prompt / timecode / repo formats. Includes `templates/lesson_steps.py.tmpl`.
- `references/03-mock-and-db.md` — how `update_mock.py` rewrites `page.tsx`, how
  `patch_db.py` PATCHes Supabase, where service-role-key lives, env path on Thrall.
- `references/04-deploy.md` — exact tarball layout, scp steps, PM2 commands, verify
  curl, rollback via `.next.bak.*` directories.
- `references/05-frontend-rules.md` — hide rules (video / timecodes / ID buttons),
  block-types white-list, mockToBlocks adapter, render order (timecodes → description
  → rest).
- `references/06-pitfalls.md` — 17 silent failure modes that will waste your hour.
  Особо критичны для эфир-страниц: #11 `.env.example` ломает prod API URL, #12 hot-patch
  chunk не инвалидирует кеш, #13 `public/intensive/*` 404 из-за app router конфликта,
  #14 Next.js standalone кеширует public/ listing (нужен PM2 restart), #15 «Материалы»
  эфира — отдельное поле БД `materials`, не blocks, #16 cabinet counters — хардкод-мок,
  #17 material card был `<div>` без href (баг репо, починен 2026-05-13).
- `references/07-video-pipeline.md` — **видео-уроки end-to-end**: Kinescope upload через TUS
  (X-Video-Title quirk), CSP frame-src для iframe, тайм-коды через AssemblyAI universal-2 +
  Sonnet по word-level транскрипту, транскрипты как `public/transcripts/lesson-N.md`.

## Video lessons pipeline (NEW, 2026-05-08)

Для уроков с видео-эфиром нужны три связанные сущности — все три в скилле автоматизированы.

### 1. Kinescope embed на странице урока

- **Frontend:** `app/intensive/lesson/[id]/page.tsx` рендерит iframe `https://kinescope.io/embed/{kinescope_video_id}?playsinline=1` через padding-top 56.25% хак (НЕ через Tailwind `aspect-video` + `absolute` — на iOS Safari лазерчатый. См. Pitfall #11 в 07).
- **Source of truth для video_id:** `intensive_lessons.kinescope_video_id` (DB) ИЛИ `LessonMock.kinescopeId` (mock fallback). Backend `/api/platform/intensive/lessons` отдаёт `kinescope_video_id` в DTO — фронт preferит DTO, mock — fallback.
- **CSP (HARD RULE):** `next.config.ts` ДОЛЖЕН содержать `frame-src 'self' https://kinescope.io https://*.kinescope.io` + `media-src` для CDN; Caddy `/etc/caddy/Caddyfile` ДОЛЖЕН отдавать тот же CSP (он перезаписывает Next-заголовок). Без этого iframe чёрный без сообщения. См. 07-video-pipeline.md секция «CSP и Caddy».
- **Upload через API:** `POST https://uploader.kinescope.io/v2/video` со всем файлом в body + `X-Video-Title` (b64 от ASCII-плейсхолдера, потому что header'ы ASCII-only) + `X-Parent-Id`. После — PATCH `/v1/videos/{id}` с настоящим title (cyrillic). См. 07 секция «Upload».

### 2. Тайм-коды по реальным переходам темы

Двухэтапный пайплайн вместо ручной разметки или равномерных интервалов:

1. **Транскрибация** в AssemblyAI: `language_code=ru`, `speech_models=["universal-2"]` (устаревший `speech_model` строкой больше не работает — fallback ругается). Получаем words с `start/end` в ms.
2. **Сегментация** в окна по 30s, отправка в Sonnet через Agent tool с просьбой найти 5-7 точек где явно меняется тема. Sonnet возвращает `{ts: int_seconds, label: "..."}`. **НЕ** генерируй тайм-коды через OpenRouter — только через `Agent(subagent_type=general-purpose, model=sonnet)` per rules.md.
3. **Запись** в DB как блоки `type=timecode` с форматом `{id, ts: "MM:SS", type, label}`, вставленные после meta/outcome/skills и перед steps. Параллельно те же тайм-коды в mock `LessonMock.timecodes[]` для SSR.

### 3. Транскрипт-файлы для скачивания

- Файлы лежат в `apps/web/public/transcripts/lesson-{N}.md` — markdown с заголовками `## MM:SS — label` по тайм-кодам и абзацами по паузам (gap > 800ms).
- Кнопка «Скачать транскрипт» на странице урока показывается между видео и тайм-кодами для `lessonN ∈ [1..5]` (расширять список по мере появления новых транскриптов). Атрибут `download="agentos-lesson-{N}-transcript.md"`.
- Транскрипт = бонус для AI-репетитор-флоу из L1: ученик скачивает .md, вставляет в Claude/GPT, расспрашивает.

См. полный пайплайн в `references/07-video-pipeline.md`.

## Templates

In `templates/`:

- `lesson_steps.py.tmpl` — copy to `/tmp/lessonN_steps.py`, fill in TITLE / DURATION /
  DESCRIPTION / OUTCOME / SKILLS / PROMPTS / REPOS / TIMECODES / STEPS.
- `update_mock.py.tmpl` — copy to `/tmp/update_mock_lN.py`, change bonus_number,
  block boundary identifiers (`'11': {` / `'12': {`).
- `patch_db.py.tmpl` — copy to `/tmp/patch_db_lN.py`, change `bonus_number=eq.N`.

## Quickstart: add a new bonus in 5 minutes

```bash
# 1. Copy templates, fill in content
cp .claude/skills/agentos-content/templates/lesson_steps.py.tmpl /tmp/lesson12_steps.py
cp .claude/skills/agentos-content/templates/update_mock.py.tmpl /tmp/update_mock_l12.py
cp .claude/skills/agentos-content/templates/patch_db.py.tmpl /tmp/patch_db_l12.py
# Edit lesson12_steps.py — add TITLE, DESCRIPTION, STEPS, etc.
# Edit update_mock_l12.py — change "'11'" → "'12'", "'12'" → "'13'" (block boundary)
# Edit patch_db_l12.py — change "bonus_number=eq.2" → "bonus_number=eq.3"

# 2. Update mock + DB
python3 /tmp/update_mock_l12.py
scp /tmp/lesson12_steps.py /tmp/patch_db_l12.py root@<your-staging-server-ip>:/root/
ssh root@<your-staging-server-ip> 'cp /root/lesson12_steps.py /tmp/lesson12_steps.py && \
  set -a && source /home/<your-user>/intensive-agentos/bot/.env && set +a && \
  cd /root && python3 patch_db_l12.py'

# 3. Build + deploy (see references/04-deploy.md for full steps)
cd apps/web && npm run build
# ... stage tarball, scp, unpack on prod server, PM2 restart, verify

# 4. Commit + push
git add apps/web/app/intensive/lesson/\[id\]/page.tsx
git commit -m "feat(lesson 12): новый бонус про X"
git push origin main
```

## Where content lives

| Layer | Location |
|---|---|
| Python source-of-truth (current session) | `/tmp/lessonN_steps.py` |
| Templates (this skill) | `.claude/skills/agentos-content/templates/` |
| TS mock (SSR fallback) | `apps/web/app/intensive/lesson/[id]/page.tsx` (`BONUS_LESSONS` / `ONBOARDING_LESSONS`) |
| Block renderer | `apps/web/components/blocks/UnifiedBlockRenderer.tsx` |
| Block types schema | `apps/web/lib/unified-block-types.ts` |
| DB (live source for client fetch) | Supabase `intensive_bonuses` table, column `blocks` (JSON) |
| Backend (FastAPI gunicorn :8095) | `/home/<your-user>/intensive-agentos/api/` on Thrall |
| Production frontend | prod server <your-prod-server-ip> → `/var/www/<your-project>/` (PM2 :3020) |
| Staging frontend | Thrall <your-staging-server-ip> → `/home/<your-user>/intensive-<your-pm2-staging-name>/` (PM2 :3010) |
| Repo | `<your-github-org>/<your-platform-repo>` (private) |
