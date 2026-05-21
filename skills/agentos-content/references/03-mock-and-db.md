# 03 — Mock layer (page.tsx) + DB layer (Supabase)

Один и тот же `/tmp/lessonN_steps.py` обновляет ОБА слоя через два скрипта.

## Mock layer — `update_mock_lN.py`

Перезаписывает блок `'N': { ... }` в `BONUS_LESSONS` объекте файла
`apps/web/app/intensive/lesson/[id]/page.tsx`.

### Что обновляется

- `title`, `duration`, `description` (single-line)
- `outcome[]`, `skills[]` (массивы)
- `timecodes[]`, `prompts[]`, `repos[]` (массивы объектов)
- `steps[]` (массив объектов с num / title / goal / body / command / resources)

### Как работает

1. Читает `lessonN_steps.py` через `sys.path.insert(0, '/tmp')`
2. Генерирует JS-литералы через `js_str()` helper:
   ```python
   def js_str(v: str) -> str:
       return "'" + v.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n') + "'"
   ```
3. Локализует блок `'N': {` ... `'N+1': {` в page.tsx
4. Через `re.sub` (с lambda — см. ниже) подменяет соответствующие поля
5. Записывает обратно

### CRITICAL: lambda обязательна в re.sub

❌ НЕ ДЕЛАЙ ТАК:
```python
block = re.sub(pattern, new_steps + '\n', block, count=1, flags=re.MULTILINE)
```
re.sub в Python ИНТЕРПРЕТИРУЕТ `\n` в replacement string как реальный newline character.
Это превратит `'sudo cmd1\\nsudo cmd2'` (валидный JS escape) в реальный newline → JS
parse error «Unterminated string constant».

✅ ДЕЛАЙ ТАК:
```python
def sub_lit(pattern, repl_str, src):
    return re.sub(pattern, lambda m: repl_str, src, count=1, flags=re.MULTILINE)

block = sub_lit(pattern, new_steps + '\n', block)
```
Lambda — это replacement function, она НЕ обрабатывает escape-последовательности.

### Шаблон

См. `templates/update_mock.py.tmpl`. При создании скрипта для нового бонуса меняй:
- `from lessonN_steps import ...` (N = номер из имени файла)
- `m_start = s.find("  '11': {")` → нужный bonus URL id
- `m_end = s.find("  '12': {", m_start)` → следующий bonus URL id (граница)

### Если бонус ПЕРВЫЙ или ПОСЛЕДНИЙ

Граница `m_end` должна быть стабильной строкой ПОСЛЕ нужного блока. Если бонус
последний — используй `};` (закрытие `BONUS_LESSONS` объекта).

### Запуск

```bash
python3 /tmp/update_mock_lN.py
# Output: "Updated mock lN: X steps, Y outcome, Z skills, W timecodes"
```

После этого проверь `git diff apps/web/app/intensive/lesson/[id]/page.tsx` — должны
обновиться только нужные поля внутри `'N': { ... }`.

## DB layer — `patch_db_lN.py`

PATCHит row в Supabase таблице `intensive_bonuses` через PostgREST.

### Что обновляется

- `title` (string)
- `description` (string)
- `blocks` (JSON array of unified blocks)

`updated_at` НЕ автоматически — это ОК, не индикатор «не применилось» (см. Pitfall #3).

### Структура блоков на выходе

```python
blocks = []
blocks.append({"id": "meta-dur-1", "type": "meta", "key": "duration", "value": "30 мин"})
blocks.append({"id": "skills-2", "type": "skills", "items": [...]})
blocks.append({"id": "outcome-3", "type": "outcome", "items": [...]})

for step in STEPS:
    blocks.append({"id": "step-N", "type": "step", "num": ..., "title": ..., "goal": ..., "body": ...})
    if step.command:
        blocks.append({"id": "code-N+1", "type": "code", "lang": "bash", "code": ..., "title": ...})

for tc in TIMECODES:
    blocks.append({"id": "tc-N", "type": "timecode", "ts": ..., "label": ...})

for prompt in PROMPTS:
    blocks.append({"id": "prompt-N", "type": "prompt", "label": ..., "text": ..., "featured": ...})

for repo in REPOS:
    blocks.append({"id": "github-N", "type": "github", "slug": ..., "desc": ...})
```

ID каждого блока — уникальный в пределах урока (`{prefix}-{counter}`).

### Где взять Supabase service-role-key

**На Thrall в `/home/<your-user>/intensive-agentos/bot/.env`** (env переменные
`SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`).

Локально на Mac mini ключа НЕТ (только anon key в `apps/web/.env.local`). Поэтому
`patch_db.py` запускается ВСЕГДА на Thrall через ssh.

### Шаги (ОБЯЗАТЕЛЬНО в этом порядке)

```bash
# 1. Скопировать source-of-truth + patch скрипт на Thrall
scp /tmp/lessonN_steps.py /tmp/patch_db_lN.py root@<your-staging-server-ip>:/root/

# 2. ОБЯЗАТЕЛЬНО: перекопировать в /tmp на Thrall
#    (sys.path подхватит свежую версию вместо stale из прошлой сессии)
ssh root@<your-staging-server-ip> 'cp /root/lessonN_steps.py /tmp/lessonN_steps.py'

# 3. Запустить patch с env из bot/.env
ssh root@<your-staging-server-ip> \
  'set -a && source /home/<your-user>/intensive-agentos/bot/.env && set +a && \
   cd /root && python3 patch_db_lN.py'
# Output: "PATCH OK. blocks: X, steps: Y"

# 4. Verify содержимое (single-line output, безопасно для чата)
ssh root@<your-staging-server-ip> \
  'set -a; source /home/<your-user>/intensive-agentos/bot/.env; set +a; \
   curl -s "$SUPABASE_URL/rest/v1/intensive_bonuses?bonus_number=eq.N&select=title" \
   -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
   -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY"'
```

### CRITICAL: НИКОГДА не выводи весь env

❌ `cat bot/.env` — утекает service-role-key.
❌ `tr "\0" "\n" < /proc/PID/environ` без grep — утекает все секреты.
✅ `cat bot/.env | grep -E "^(SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY)" | sed 's/=.*/=PRESENT/'`
   — только маски.

См. Pitfall #5.

### CRITICAL: PATCH content-range 0-0/* НЕ означает 0 rows updated

PostgREST возвращает `content-range: 0-0/*` потому что не указан `Prefer: count=`.
Это НЕ значит, что rows не обновились. Чтобы проверить — сделай GET после PATCH
и сравни поля.

### Шаблон

См. `templates/patch_db.py.tmpl`. Меняй:
- `from lessonN_steps import ...`
- `bonus_number=eq.N`
- `value: "30 мин"` (DURATION в meta-блоке)

## Если контент не обновляется на сайте

См. Pitfall #2 (stale `/tmp` на Thrall). Чек-лист:

1. `cat /tmp/lessonN_steps.py | head -3` на Thrall — это правильная версия?
2. `python3 patch_db_lN.py` — что print'ит? (должно быть `PATCH OK. blocks: X`)
3. `curl ... select=blocks` — first step.title совпадает с тем, что в Python source?
4. Hard reload браузера (Cmd+Shift+R) — может это просто client-cache.
