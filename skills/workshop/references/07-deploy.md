# 07 — Деплой воркшопа

Единственный способ выкатить изменения на `<your-workshop-domain>` — `bash scripts/deploy.sh`. Скрипт делает всё: валидацию EN-паритета, бэкап, rsync, HTTP-verify, автоматический rollback при ошибках.

## Важно

Воркшоп — **staging-like**, не sales-лендинг. Деплой идёт автономно без явного OK user, в отличие от `<your-domain>/price` (там deploy только после «да, на prod»).

## Использование

```bash
cd /tmp/online-workshop-edgelab

# Проверить EN-паритет без деплоя
bash scripts/deploy.sh --check-only

# Задеплоить только конкретный день (RU+EN)
bash scripts/deploy.sh day-2

# Задеплоить всё (главная + все 4 дня)
bash scripts/deploy.sh day-all

# Без аргумента = day-all
bash scripts/deploy.sh
```

## Target map

| Target | Что обновится |
|---|---|
| `day-0` | `/day-0/index.html` RU + `/en/day-0/index.html` EN |
| `day-1` | `/day-1/` RU + EN |
| `day-2` | `/day-2/` RU + EN |
| `day-3` | `/day-3/` RU + EN |
| `day-all` | Полный rsync `site/` → `$REMOTE_PATH/` (с `--delete`) |

При `day-N` главная (`index.html`) НЕ трогается. Хочешь обновить главную + день одновременно — используй `day-all` или задеплой дважды.

## Что происходит внутри скрипта (6 шагов, обновлено 2026-04-24, коммит 919b7e2)

### 1. EN Sync Check

Для каждого `site/day-*/index.html` проверяется, что `site/en/day-*/index.html`:
- существует
- **не короче RU более чем на 30%** (иначе — stale placeholder)

Если есть расхождения — интерактивный prompt «Continue anyway? (y/N)». Отвечай `n`, пока EN не синхронизирован. В `--check-only` режиме просто exit 1.

### 2. Prod Drift Check (новое)

Скрипт скачивает ключевые файлы с прода, сравнивает с git. Если расходятся — стоп и три варианта:

- `[p] Pull` — скачать прод → git (сохранить правки, потом закоммитить локально)
- `[f] Force` — перезаписать прод из git (затрёт ручные правки на проде)
- `[q] Quit` — ничего не делать

Зачем: решает проблему потери правок, когда кто-то (агент или человек) менял прод напрямую через SSH без коммита. Раньше `rsync --delete` в фазе 3 незаметно съедал такие изменения.

### 3. Backup

SSH на `root@<your-prod-server-ip>`, создаёт:
```
/tmp/edgelab-workshop-backup-YYYYMMDD-HHMMSS.tar.gz
```
Содержит полный текущий `/var/www/<your-workshop>/` прод-директории.

**Важно:** файлы бэкапов копятся на prod `/tmp/` бессрочно. Раз в месяц (или когда место кончается) — `ssh root@<your-prod-server-ip> "ls -lht /tmp/edgelab-workshop-backup-*.tar.gz | tail -n +20 | xargs rm"` (оставить последние 20, удалить старые).

### 4. Deploy (rsync)

- `day-all`: `rsync -avz --delete site/ $REMOTE:/var/www/<your-workshop>/`
  - `--delete` удаляет на проде то, чего больше нет в локальном `site/`. Осторожно с этим — если случайно удалил файл локально, он уйдёт и с прода.
- `day-N`: `rsync -avz site/day-N/index.html $REMOTE:.../day-N/index.html` + аналогично для EN. **Без** `--delete`.

### 5. Verify

Проходит по всем соответствующим URL (scope зависит от target), делает `curl -o /dev/null -w "%{http_code}"`. Все должны вернуть 200.

- `day-all` проверяет: `/`, `/day-0/`…`/day-3/`, `/en/`, `/en/day-0/`…`/en/day-3/` (10 страниц)
- `day-N` проверяет: `/`, `/day-N/`, `/en/day-N/` (3 страницы)

Если хоть одна вернула не 200 — интерактивный prompt «Rollback from backup? (y/N)».

### 6. Auto-commit + push (новое)

После успешного verify скрипт сам делает `git add site/ && git commit -m "<авто-сообщение>" && git push origin main`. Git всегда в синхроне с продом, ручной commit больше не нужен.

Если скрипт закоммитил что-то лишнее (staged файлы вне `site/`) — это баг, репортить staging serverу.

## Когда деплой фейлится

### EN отстаёт от RU

Скрипт говорит `STALE: en/day-N/index.html (X lines vs RU Y lines)`. Открой оба файла, сравни, синхронизируй структуру.

Частая причина: ты добавил блок только в RU-версию. Надо зеркалить.

### 404/500 на verify

1. SSH: `ssh root@<your-prod-server-ip> "ls /var/www/<your-workshop>/day-N/"` — проверить что файл там есть.
2. Caddy логи: `ssh root@<your-prod-server-ip> "journalctl -u caddy --since '10m ago' | tail -50"`.
3. Проверить `index.html` прав: должен быть `-rw-r--r--`. Если нет — `ssh ... "chmod 644 /var/www/<your-workshop>/day-N/index.html"`.
4. Если не находится — откатить из бэкапа и разобраться локально.

### Rollback вручную

Если ты ответил `n` на автоматический rollback prompt, но потом передумал:

```bash
BACKUP_PATH="/tmp/edgelab-workshop-backup-YYYYMMDD-HHMMSS.tar.gz"
ssh root@<your-prod-server-ip> "rm -rf /var/www/<your-workshop> && tar xzf $BACKUP_PATH -C /"
```

Проверь: `curl -sS -o /dev/null -w "%{http_code}\n" https://<your-workshop-domain>/`.

## Commit + push в репо

**Обновлено 2026-04-24 (коммит 919b7e2):** скрипт делает commit + push автоматически в шаге 6. Ручной git add/commit больше не нужен. Репо `<your-github-org>/<your-workshop-repo>` приватный — push автономно.

Если нужен кастомный commit message — закоммить локально перед `deploy.sh`, скрипт увидит чистое дерево и не будет дублировать коммит.

## Где что лежит на проде

| Путь | Что это |
|---|---|
| `/var/www/<your-workshop>/` | Root вебсервера |
| `/var/www/<your-workshop>/index.html` | RU главная |
| `/var/www/<your-workshop>/day-N/index.html` | RU день |
| `/var/www/<your-workshop>/en/index.html` | EN главная |
| `/var/www/<your-workshop>/en/day-N/index.html` | EN день |
| `/tmp/edgelab-workshop-backup-*.tar.gz` | Бэкапы от deploy-скрипта |
| `/etc/caddy/Caddyfile` | Caddy config (auto-TLS через Let's Encrypt) |

## Что НЕ делать

- **НЕ запускать `npm run build` или какой-либо build-шаг на проде.** Сайт чисто статический, весь HTML уже в `site/`.
- **НЕ править файлы напрямую на проде через SSH/nano.** Все правки через git + deploy. Иначе следующий `rsync --delete` снесёт твои изменения.
- **НЕ коммитить без deploy ИЛИ deploy без коммита.** Репо = источник правды, прод = зеркало. Расхождение — источник багов.
- **НЕ использовать `scp`, `rsync`, прямой SSH-edit вручную.** ТОЛЬКО `scripts/deploy.sh` — гарантирует drift-check + backup + verify + auto-commit. Это hard rule для ВСЕХ агентов (staging server, coordinator, Claude Code, content agent).
- **НЕ деплоить если `git status` грязный на несмежных файлах.** Коммить или stash'и нерелевантные изменения — потом не поймёшь что попало на прод.
