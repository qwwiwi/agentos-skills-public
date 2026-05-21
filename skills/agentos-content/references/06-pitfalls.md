# 06 — Pitfalls (silent failures, которые съедят твой час)

Реальные ловушки, в которые попалась coordinator при подготовке lessons 10-11.
Read this before starting work — каждая стоила 15-30 минут отладки.

## Pitfall 1: re.sub `\n` в replacement string → JS parse error

### Симптом
После `python3 update_mock_lN.py` запускаешь `npm run build` → падает с
«Unterminated string constant» где-то посреди command строки. Multi-line bash командa
оказывается размазана на несколько строк JS.

### Корень
`re.sub(pattern, replacement, ...)` в Python ИНТЕРПРЕТИРУЕТ `\n` в replacement как
литеральный newline character, даже если в Python source это `\\n` (2 chars). Lambda
replacement function НЕ обрабатывает escapes.

### Фикс
```python
# ❌
block = re.sub(pattern, new_steps + '\n', block, count=1, flags=re.MULTILINE)

# ✅
def sub_lit(pattern, repl_str, src):
    return re.sub(pattern, lambda m: repl_str, src, count=1, flags=re.MULTILINE)

block = sub_lit(pattern, new_steps + '\n', block)
```

В шаблоне `templates/update_mock.py.tmpl` это уже исправлено.

### Ранний детектор
После `update_mock.py` сделай:
```bash
cd apps/web && python3 -c "
data = open('app/intensive/lesson/[id]/page.tsx').read().splitlines()
for i, l in enumerate(data):
    if i > 240 and i < 260:  # район проблемного шага
        print(repr(l))
"
```
Если видишь `'sudo cmd1'` на одной строке и `'sudo cmd2'` на следующей — баг есть.
Должно быть `'sudo cmd1\\nsudo cmd2'` на одной строке.

## Pitfall 2: stale `/tmp/lessonN_steps.py` на Thrall

### Симптом
`patch_db_lN.py` print'ит `PATCH OK. blocks: 45, steps: 20` (вроде ок), но в Supabase
лежит контент СТАРОЙ версии. Браузер показывает: новый mock мелькнёт на 100ms → клиент
делает API fetch → подменяет на старую версию из DB.

### Корень
`patch_db.py` делает `sys.path.insert(0, '/tmp')` — ищет `lessonN_steps.py` в `/tmp`.
Если ты `scp` файл в `/root/` (потому что нет permission на `/tmp/`), а в `/tmp/` ещё
лежит файл от прошлой сессии — Python загружает СТАРУЮ версию из `/tmp/`. Patch
улетает корректно, но с устаревшим контентом.

### Фикс — обязательный шаг

```bash
# 1. scp в /root (нельзя в /tmp потому что owned by openclaw)
scp /tmp/lessonN_steps.py /tmp/patch_db_lN.py root@<your-staging-server-ip>:/root/

# 2. ОБЯЗАТЕЛЬНО: перекопировать в /tmp
ssh root@<your-staging-server-ip> 'cp /root/lessonN_steps.py /tmp/lessonN_steps.py'

# 3. Только теперь — patch
ssh root@<your-staging-server-ip> \
  'set -a && source /home/<your-user>/intensive-agentos/bot/.env && set +a && \
   cd /root && python3 patch_db_lN.py'
```

### Verify

После patch — обязательно прочитай назад:
```bash
ssh root@<your-staging-server-ip> \
  'set -a; source /home/<your-user>/intensive-agentos/bot/.env; set +a; \
   curl -s "$SUPABASE_URL/rest/v1/intensive_bonuses?bonus_number=eq.N&select=blocks" \
   -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
   -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY"' | python3 -c "
import json, sys
r = json.load(sys.stdin)[0]
steps = [b for b in r['blocks'] if b['type']=='step']
print('first step:', steps[0]['title'][:60])
print('last step:', steps[-1]['title'][:60])
"
```

`first step` и `last step` должны совпадать с тем, что в твоём
`lessonN_steps.py STEPS[0]` и `STEPS[-1]`.

## Pitfall 3: PATCH `content-range: 0-0/*` НЕ значит 0 rows updated

### Симптом
PATCH через PostgREST → HTTP 200, но header `content-range: 0-0/*`. Кажется, что
0 rows updated — но фактически они обновились.

### Корень
PostgREST показывает реальный count только если в запросе `Prefer: count=exact`
(или `count=planned`). Без него `0-0/*` — это «count not requested», не «zero rows».

### Фикс
Не паникуй. Сделай GET сразу после PATCH и сравни fields. Если изменения видны — всё
ок. Если хочешь явный count в response, добавь header `Prefer: count=exact, return=representation`.

## Pitfall 4: macOS xattr warnings в tar

### Симптом
```
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
```
В выводе на сервере при unpack.

### Корень
macOS добавляет `com.apple.provenance` xattr ко всем файлам, скачанным из интернета
(Gatekeeper). bsdtar в macOS их сохраняет, GNU tar в Linux — игнорирует и warning'ает.

### Фикс
Косметика. Игнорируй или `2>/dev/null` в команде распаковки. На функциональность не влияет.

## Pitfall 5: secrets в Bash output

### Симптом
Случайно сделала `tr "\0" "\n" < /proc/PID/environ` чтобы посмотреть env процесса —
`SUPABASE_SERVICE_ROLE_KEY` (root-доступ к DB) утёк в чат user.

### Корень
Любая команда, которая выводит env / config / .env файл целиком — утечёт всё
содержимое в stdout, который попадает в чат / логи / возможно в публичный канал.

### Фикс
Всегда фильтруй вывод. Маски вместо values:

```bash
# ❌
cat bot/.env
tr "\0" "\n" < /proc/PID/environ

# ✅ — только маска ключа
cat bot/.env | grep -E "^(SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY)" | sed 's/=.*/=PRESENT/'
sudo tr "\0" "\n" < /proc/PID/environ | grep -iE "supabase_url|service_role" | sed 's/=.*/=PRESENT/'

# ✅ — value только если оно безопасно (URL, путь, не токен)
echo "SUPABASE_URL: $SUPABASE_URL"  # URL ок, ключ — никогда
```

Если ключ всё-таки утёк — нужна ротация через Supabase Dashboard → Project Settings →
API → Reset service_role key. И обновить во всех `.env` файлах на всех серверах.

## Pitfall 6: client-side fetch override

### Симптом
Залил mock в page.tsx, видишь правильный контент при reload → через 100ms он
заменяется старым. Кажется «закешировался».

### Корень
SSR показывает mock (новый). Через `useEffect` фронт делает `apiClient.get('/api/platform/intensive/bonus/N')`
и `setApiOverride(dto)` → re-render с DB content. Если DB старая → видишь подмену.

### Фикс
Обнови DB через `patch_db_lN.py`. Mock — только fallback для случаев когда API
недоступен (anon-сессия, 401, 404, abort).

См. `01-architecture.md` секция «Data flow при загрузке страницы».

## Pitfall 7: Wrong deploy target (Thrall vs prod server)

### Симптом
Задеплоила на Thrall PM2 `<your-pm2-name>` — все curl 127.0.0.1:3020 на Thrall
зелёные. Принц видит старый код. Нет alerting'а — просто silent old version.

### Корень
DNS `<your-agentos-domain>` → <your-prod-server-ip> (prod server), не Thrall. На Thrall есть PM2
`<your-pm2-name>` — это shadow-instance, dormant.

### Фикс
Перед deploy: `dig +short <your-agentos-domain>` → должно быть `<your-prod-server-ip>`. Если
видишь Thrall IP — DNS изменился, спроси user.

Production deploy ВСЕГДА на prod server <your-prod-server-ip> (см. `04-deploy.md`).

## Pitfall 8: regex `.*?` не захватывает multi-line array-блоки

### Симптом
После `update_mock_lN.py` title / skills / steps обновились корректно, но
`repos:` (или `outcome:`, или `timecodes:`) **остался от предыдущей версии**.
На странице снизу висят чужие GitHub-блоки, или старый список outcome'ов не
заменился. Smoke `grep` на новые значения проходит (они есть в DOM), но
старые не удалились.

### Корень
В `update_mock_lN.py` regex написан как `r"^    repos: \[.*?\],\n"`. `.*?` —
non-greedy match **в пределах одной строки**. Multi-line блок вида:

```ts
    repos: [
      { slug: '...', desc: '...' },
      { slug: '...', desc: '...' },
    ],
```

этот regex НЕ матчит — `.` не захватывает `\n` без `re.DOTALL`. Результат:
старый блок остаётся как есть, новый не пишется (sub_lit count=1 не находит
куда вставить).

### Фикс

```python
# ❌ — single-line only
block = sub_lit(r"^    repos: \[.*?\],\n", new_repos + '\n', block)

# ✅ — multi-line через (?:.*\n)*?
block = re.sub(
    r"^    repos: \[(?:.*\n)*?    \],\n",
    lambda m: new_repos + '\n',
    block, count=1, flags=re.MULTILINE,
)
```

Применяется ко всем array-блокам которые могут быть multi-line: `repos`,
`outcome`, `timecodes`, `prompts`, `steps`. Если текущий шаблон uses
`sub_lit` со single-line `.*?` — менять на explicit multi-line pattern.

В `templates/update_mock.py.tmpl` pattern для `outcome` и `timecodes` уже
multi-line (`(?:.*\n)*?`). Pattern для `repos` исправлен 2026-05-06 после
incident на lesson 12.

### Ранний детектор — visual verify (см. Pitfall 9)
Проблема выявилась только через скриншот mobile-page userем. `grep` на новые
значения отрапортовал «есть», но не проверил отсутствие старых. Visual
verify ловит этот класс багов автоматически.

## Pitfall 9: verify after deploy = visual, не только grep (HARD RULE)

### Симптом
После deploy я отрапортовала «Готово, <your-github-org>/twitter и telegram-chip на
проде». Принц открыл страницу через Chrome → внизу 3 чужих GitHub-блока
от старой версии бонуса (`anthropics/skills`, `<your-github-org>/public-architecture-claude-code`,
`<your-github-org>/senior-brainstorm-skill`).

### Корень
Verify был только positive: `grep "<your-github-org>/twitter" → есть → Готово`. Не было
negative test: «нет ли лишних элементов от прошлой версии». `grep` ловит
наличие, не отсутствие. Принц увидел сразу глазами через скриншот.

### Фикс — обязательный шаг после ЛЮБОГО UI-deploy

```bash
# 1. agent-browser (CDP automation) — открыть страницу в headless Chrome
# Скилл: ~/.claude/skills/agent-browser/SKILL.md (v0.25.3+)

# 2. Mobile viewport (375px width — типичный iPhone)
# У user mobile-first интерфейс, всё критичное проверять в mobile

# 3. Screenshot full-page (не только viewport)
# Проскроллить страницу полностью, поймать всё включая footer

# 4. Глазами сверить с ожиданием
# Положительный test: всё что должно быть — есть и на правильных местах
# Негативный test: ничего лишнего от прошлой версии не осталось

# 5. Только теперь рапорт «Готово»
```

### Что говорить user

- ✅ «Задеплоила, проверила визуально через agent-browser, скриншот mobile —
  выглядит как ожидалось»
- ❌ «Задеплоила, HTTP 200, grep на ключевые строки прошёл — Готово»
  (без visual verify это incomplete)
- ⚠️ Если визуальную проверку **не делала** (например agent-browser недоступен) —
  явно сказать: «визуально не проверила через браузер, могут быть остаточные UI-элементы»

### Применяется ко всем UI-задачам

EdgeLab, AgentOS Intensive, workshop, любой деплой на <your-domain> /
<your-agentos-domain> / staging.<your-agentos-domain> / любая страница которую
видит ученик / user.

Не применяется: изменения backend без UI (API endpoints, scripts, cron),
изменения скрытые от пользователя (логи, метрики).

## Pitfall 10: контент урока живёт в 4 местах, не в одном

### Симптом
Обновила контент урока (DB `intensive_lessons.blocks` + `BONUS_LESSONS`
mock в page.tsx). Smoke на детальной странице `/intensive/lesson/N`
показывает новый контент. Принц открывает **другую страницу** (cabinet
с listing'ом или materials с агрегацией) — там старые названия / заглушка.

### Корень
Содержание урока в нашей платформе sourced из **четырёх разных мест**:

| Где | Что хранит | Кто читает |
|---|---|---|
| `intensive_lessons` table (Supabase) | Полный контент урока (blocks JSON) | Детальная страница `/intensive/lesson/N` через API |
| `ONBOARDING_LESSONS` mock в `app/intensive/lesson/[id]/page.tsx` | SSR fallback для уроков 1-5 | `/intensive/lesson/N` (если API не отвечает) |
| `BONUS_LESSONS` mock в том же файле | SSR fallback для бонусов 10-12 | `/intensive/lesson/N` (для bonus_number) |
| `LESSONS[]` hardcoded в `app/intensive/cabinet/onboarding/page.tsx` | Список предобучения (titles + meta) | Cabinet → onboarding listing |
| `FEED_ITEMS[]` hardcoded в `app/intensive/materials/page.tsx` | Агрегация всех материалов | Materials feed |

Когда обновляешь содержимое урока, нужно ОБОЙТИ все эти места. Иначе
listing-страницы покажут старые названия / заглушки.

### Фикс — обязательный grep-чеклист после изменения урока

```bash
# 1. Найти все hardcoded mock'и связанные с уроком/бонусом
cd apps/web
grep -rn "ONBOARDING_LESSONS\|BONUS_LESSONS\|FEED_ITEMS\|LESSONS\[" app/

# 2. Найти все страницы которые ссылаются на /intensive/lesson
grep -rn "intensive/lesson/" app/intensive/

# 3. Проверить каждый найденный файл — нужно ли там обновить:
#    - title / название урока
#    - meta-строку (длительность, теги)
#    - href (если URL изменился)
#    - count в FILTER_LABELS (если добавил/удалил материал)
```

### Где обновлять что

| Изменение | Файлы для обновления |
|---|---|
| Контент урока (steps, prompts, etc) | `intensive_lessons.blocks` (DB) + `BONUS_LESSONS`/`ONBOARDING_LESSONS` mock |
| Title или duration урока | DB title + mock title + `cabinet/onboarding/page.tsx LESSONS[]` + `materials/page.tsx FEED_ITEMS[]` |
| Удалить/переименовать урок | Все 4 места выше + проверить ссылки в других уроках (cross-references) |
| Добавить новый материал (репо/Gist/ссылка) | `materials/page.tsx FEED_ITEMS[]` + `FILTER_LABELS` count |

### Ранний детектор
Visual verify (Pitfall #9) ловит это автоматически — если открыть
**listing-страницы** (cabinet/onboarding + materials), а не только
детальную страницу урока. После любого изменения контента урока:
- скриншот `/intensive/lesson/N` (детали)
- скриншот `/intensive/cabinet/onboarding` (список предобучения)
- скриншот `/intensive/materials` (агрегация)

Если только первое — пропустишь рассинхрон названий и старые заглушки.

## Pitfall 11: `NEXT_PUBLIC_API_BASE_URL` из `.env.example` ломает prod

### Симптом
Деплой проходит, build зелёный, страница рендерится. При клике на эфир — «Не удалось загрузить эфир». В DevTools Network запросы летят на `https://api.<your-agentos-domain>/...` и возвращают DNS-fail или 404.

### Корень
`apps/web/.env.example` содержит **staging-значение** `NEXT_PUBLIC_API_BASE_URL=https://staging-api.<your-agentos-domain>`. Скопировал «как пример» в `.env.production` (или просто оставил из .env.example) → попало в build → все API запросы летят в subdomain которого нет в Caddy на prod server.

### Фикс
**Перед сборкой ВСЕГДА читать README.md репо.** В разделе «Build-time public переменные» явно указано prod-значение:
```
NEXT_PUBLIC_API_BASE_URL=https://<your-agentos-domain>  (prod, same-origin через Caddy /api/*)
NEXT_PUBLIC_API_BASE_URL=https://staging.<your-agentos-domain>  (staging)
```
`.env.example` — это шаблон, не prod-конфиг. Никогда не доверяй ему вслепую.

### Ранний детектор
После `npm run build` перед деплоем:
```bash
grep -rhoE 'https://[a-z.-]+\.edgelab\.su' .next/static/chunks/ | sort -u
```
Если видишь `api.<your-agentos-domain>` или `staging-api.<your-agentos-domain>` в prod-сборке — fix env и пересобирай.

Зафиксировано в `core/rules.md` как hard rule: «Before editing/building/deploying production: READ the repo's README first».

## Pitfall 12: Hot-patch chunk с прежним hash не инвалидирует браузерный кеш

### Симптом
Заменил один JS-файл в `.next/static/chunks/...` поверх (с тем же именем). На своём ноуте clear-session браузер видит свежий код. У user на мобильном Safari — старый. Думаешь «у него кэш» — но и через несколько часов то же.

### Корень
Next.js generates filename like `cabinet/page-bed51e1ec24382d3.js` где hash из контента. HTML страницы (от server.js) ссылается на этот hash. Если ты правишь содержимое файла, но имя оставляешь — браузер уже скачал именно этот hash и не запрашивает заново (immutable cache). Новые посетители (без кэша) получат новый код, существующие — нет.

### Фикс
**Не делать hot-patch скомпилированных chunks.** Всегда полный `npm run build` (получит новый hash), tarball, scp, `pm2 restart`. Стоит 5 минут — экономит часы непонимания «у меня работает, у тебя нет».

Если ОЧЕНЬ нужен hot-patch — менять и chunk-файл, и `app-build-manifest.json` / `build-manifest.json` где этот hash прописан. Слишком хрупко, не стоит.

### Ранний детектор
```bash
# До деплоя — сравни hash в HTML с реальным файлом
curl -sS https://<your-agentos-domain>/intensive/cabinet | grep -oE 'cabinet/page-[a-z0-9]+\.js' | sort -u
# Должен совпадать с .next/static/chunks/app/intensive/cabinet/page-*.js
```

## Pitfall 13: статика в `public/intensive/*` → 404 (app router конфликт)

### Симптом
Положил HTML файлы в `public/intensive/eth2/step-1.html`, сделал PM2 restart, запрос `https://<your-agentos-domain>/intensive/eth2/step-1.html` → HTTP 404. А `public/favicon.ico` и `public/transcripts/lesson-1.md` отдаются 200.

### Корень
Next.js app router имеет роуты `/intensive/cabinet`, `/intensive/eth/[id]`, `/intensive/lesson/[id]`, `/intensive/profile` и т.д. Когда запрос приходит на `/intensive/eth2/...`, app router пытается матчить — не находит, возвращает 404 БЕЗ fallback в `public/`. Public/ обслуживается только для путей которые app router НЕ собирается обрабатывать.

### Фикс
Положить статику ВНЕ `/intensive/*`. Паттерн уже в проекте — Эфир 1 живёт в `public/efir-1/step-N.html` → URL `https://<your-agentos-domain>/efir-1/step-N.html`. Используй такой же:
```
public/efir-2/step-N.html   → /efir-2/step-N.html   ✓
public/efir-3/...           → /efir-3/...           ✓
public/intensive/eth2/...   → /intensive/eth2/...   ✗ 404
```

### Ранний детектор
После scp — `curl -o /dev/null -w "%{http_code}\n" <url>` хотя бы одного файла. Если 404 при существующем файле в `public/` — путь конфликтует с app router.

## Pitfall 14: Next.js standalone кеширует список `public/` при старте

### Симптом
Скопировал новые HTML файлы в `public/efir-2/`, проверил curl → 404. Проверил `ls` на сервере — файлы на месте, права корректные. Не работает.

### Корень
Next.js standalone server (`server.js`) индексирует `public/` при инициализации. Файлы добавленные ПОСЛЕ старта процесса не видны до рестарта PM2.

### Фикс
После любых изменений в `public/` (новые файлы, переименование, удаление) — обязательно `pm2 restart <your-pm2-name>`. После рестарта индекс пересоберётся, новые файлы будут доступны.

### Ранний детектор
Авто: после scp в public всегда делай `pm2 restart` той же командой, без размышлений. Не строй гипотезы про «должно работать» — это правило, не догадка.

## Pitfall 15: «Материалы» эфира = поле `intensive_eth_details.materials`, не `blocks`

### Симптом
Добавил 10 link-блоков `{type:"link", kind:"doc", href:"...", label:"..."}` в `intensive_eth_details.blocks` после соответствующих step-блоков. На странице эфира они отображаются как inline-ссылки под каждым шагом (правильно). Но вкладка-счётчик в шапке всё равно показывает «Материалы · 0».

### Корень
`apps/web/app/intensive/eth/[id]/page.tsx` источник материалов:
```ts
files: asMaterialArray(dto.materials),  // ← НЕ blocks!
const materialsCount = d.files.length;
```
Поле `materials` — отдельный JSONB-массив в `intensive_eth_details`, со схемой `{name, desc, url, filename}` (фронт парсит именно эти ключи). Блоки `type:"link"` внутри `blocks` рендерятся как inline-контент описания, но НЕ попадают во вкладку «Материалы».

### Фикс
PATCH `intensive_eth_details.materials` с массивом объектов схемы Эфира 1:
```python
materials = [
    {
        "url": f"/efir-2/step-{n}.html",
        "desc": "короткое описание для тизера",
        "name": f"Шаг {n} · название",
        "filename": f"step-{n}.html"
    }
    for n in range(1, 11)
]
```

Можно одновременно держать и link-блоки внутри `blocks` (для inline под шагом), и `materials` (для вкладки) — это две разные UX-точки. Эфир 1 использует именно так.

### Ранний детектор
После PATCH блоков всегда:
```sql
select session_number, jsonb_array_length(materials) as mat_count from intensive_eth_details order by session_number;
```
Эфир 1 имеет 5-6 материалов — целевой ориентир. Если у нового эфира 0 — забыли заполнить.

## Pitfall 16: Cabinet карточки счётчик материалов — хардкод-мок в page.tsx, не DB

### Симптом
PATCH `intensive_eth_details.materials` сделан, на странице эфира вкладка «Материалы · 10» корректная. Но в кабинете на главной карточка «02 Проект с нуля · 0 материала · 0 урока». Странно — у Эфира 1 «5 материала» хотя у меня в БД у него 6.

### Корень
`apps/web/app/intensive/cabinet/page.tsx` имеет массив `BROADCASTS` с хардкод-моком:
```ts
const BROADCASTS = [
  { id: 1, num: '01', title: 'Настройка Claude Code', materials: 5, lessons: 0, open: true },
  { id: 2, num: '02', title: 'Проект с нуля', materials: 0, lessons: 0, open: true },
  ...
];
```
Ничего не читается из БД. Поля `materials`, `lessons`, `open` — статика. Используется для скорости (не нужно ждать API на главной кабинета) и для возможности «открыть» эфир до того как реально загружены материалы.

### Фикс
При добавлении материалов к эфиру N — параллельно править мок:
```diff
- { id: N, num: '0N', title: '...', materials: 0, lessons: 0, open: false },
+ { id: N, num: '0N', title: '...', materials: <реальное число>, lessons: 0, open: true },
```
Затем полный rebuild + deploy. Никак не обойдёшься без редеплоя — этот файл сериализуется в client chunk на build-time.

### Ранний детектор
После любого PATCH `intensive_eth_details.materials` для эфира — открыть `apps/web/app/intensive/cabinet/page.tsx`, проверить что в `BROADCASTS[id-1].materials` стоит то же число.

## Pitfall 17: карточка материала на странице эфира — `<div>` без href (баг репо)

### Симптом
Материалы во вкладке «Материалы» рендерятся как красивая карточка с иконкой файла + иконкой стрелки. Hover ничего не делает, клик ничего не делает.

### Корень
`apps/web/app/intensive/eth/[id]/page.tsx:447-461` рендерит каждую материал-карточку как `<div>` без `href`/`onClick`. URL из `materials[i].url` нигде не использовался. Баг был с самого начала — у Эфира 1 та же проблема, просто пользователи не пробовали кликать.

### Фикс (применён 2026-05-13)
1. `MaterialItem` interface — добавить `url: string | null`
2. `asMaterialArray` — подбирать `r.url`
3. Рендерер: если `file.url` есть → обернуть в `<a href={file.url} target="_blank" rel="noopener noreferrer">`, иначе оставить `<div>` для backward-compat. Заменить иконку «↓» на «→» (это не download, это переход).

Commit pending. Если переоткроется — взять снова из этого pitfall.

### Ранний детектор
После любого contentful изменения страницы эфира — попробовать кликнуть карточку материала в браузере. Если ничего не открылось — рендерер сломан.
