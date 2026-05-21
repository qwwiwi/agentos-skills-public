# 04 — Deploy pipeline (build → tarball → prod server → PM2)

## Куда деплой

| Env | Host | Path | PM2 name | Port | DNS |
|---|---|---|---|---|---|
| **PROD** | prod server <your-prod-server-ip> | `/var/www/<your-project>/` | `<your-pm2-name>` | 3020 | `<your-agentos-domain>` |
| Staging | Thrall <your-staging-server-ip> | `/home/<your-user>/intensive-<your-pm2-staging-name>/` | `<your-pm2-staging-name>` | 3010 | `staging.<your-agentos-domain>` |

⚠️ **На Thrall тоже есть PM2 `<your-pm2-name>` на :3020 — это shadow-instance,
к публичному домену НЕ подключён.** Деплой только туда = «зелёный» curl на `127.0.0.1`,
но prince видит старый код. Всегда `dig +short <your-agentos-domain>` перед deploy.

## Production deploy — пошагово

### 1. Build (локально на Mac mini)

```bash
cd ~/projects/intensive-agentos-platform/apps/web
npm run build
# Smoke: должно завершиться без TypeScript / webpack ошибок
```

⚠️ **НИКОГДА не запускай `npm run build` на prod server / Thrall.** На production
серверах нет dev-зависимостей.

### 2. Stage standalone в /tmp

Next.js 15 standalone build кладёт файлы в `.next/standalone/` (без `.next/static`
и без `public/` — нужно собирать вручную).

```bash
# Используй уникальное имя stage dir чтобы не конфликтовать с прошлыми
STAGE=/tmp/web-stage-$(date +%s)
mkdir -p $STAGE/.next
cp -R apps/web/.next/standalone/. $STAGE/
cp -R apps/web/.next/static $STAGE/.next/static
cp -R apps/web/public $STAGE/public
tar -czf /tmp/web-deploy.tgz -C $STAGE .
ls -lh /tmp/web-deploy.tgz  # обычно ~16 MB
```

### 3. Upload на prod server

```bash
scp /tmp/web-deploy.tgz root@<your-prod-server-ip>:/tmp/web-deploy.tgz
```

### 4. Unpack + restart на prod server

```bash
ssh root@<your-prod-server-ip> 'set -e
cd /var/www/<your-project>

# (опц.) backup .next перед перезаписью — на случай rollback
cp -R .next /tmp/agentos-prod-next.bak.$(date +%Y%m%d%H%M%S)

# Очистить старые server / static / BUILD_ID, оставив node_modules
rm -rf .next/server .next/static .next/BUILD_ID

# Распаковать новый билд (--overwrite важно)
tar -xzf /tmp/web-deploy.tgz -C . --overwrite 2>/dev/null

# Восстановить ownership (uid 501 = openclaw, group root по конвенции)
chown -R 501:root .

# Restart PM2 (--update-env берёт свежие env vars если они изменились)
pm2 restart <your-pm2-name> --update-env

# Подождать health
sleep 3 && pm2 list | grep agentos'
```

### 5. Verify

```bash
# Локально на prod server (внутренний порт)
ssh root@<your-prod-server-ip> 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3020/intensive/lesson/N'

# Публично (через Caddy)
curl -s -o /dev/null -w "%{http_code}\n" https://<your-agentos-domain>/intensive/lesson/N

# Должно быть 200 на обоих
```

### 6. Smoke контента

```bash
curl -s "https://<your-agentos-domain>/intensive/lesson/N" | \
  grep -oE "(заголовок_шага_1|финальный_шаг|ключевая_фраза)" | sort -u
```

Должны появиться ключевые фразы из твоего контента.

## Rollback

Если задеплоился сломанный билд:

```bash
ssh root@<your-prod-server-ip> 'cd /var/www/<your-project> && \
  ls -t .next.bak.* | head -1'
# → .next.bak.20260506-220218

ssh root@<your-prod-server-ip> 'cd /var/www/<your-project> && \
  rm -rf .next && \
  cp -R .next.bak.YYYYMMDD-HHMMSS .next && \
  pm2 restart <your-pm2-name>'
```

Бэкапы могут жить долго — иногда чисти `.next.bak.*` (они каждый по 50-100 MB).

## Cosmetic warnings

`tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'` —
это macOS xattr, безвредно. Игнорируй / `2>/dev/null`.

## Staging deploy

Аналогично, но:
- scp на `root@<your-staging-server-ip>`
- path `/home/<your-user>/intensive-<your-pm2-staging-name>/`
- pm2 restart `<your-pm2-staging-name>`
- verify `https://staging.<your-agentos-domain>/intensive/lesson/N`

Staging — автономно (без OK user). Production — **только** с явным «да, на prod».

## Commit + push

После успешного prod-деплоя:

```bash
cd ~/projects/intensive-agentos-platform

git add apps/web/app/intensive/lesson/\[id\]/page.tsx
# Если менял UnifiedBlockRenderer / unified-block-types — добавь и их

git commit -m "feat(lesson N): краткое описание

Детали изменения. Что добавлено / переписано / удалено.
Ссылка на источник или контекст." 

git push origin main
```

Репо: `<your-github-org>/<your-platform-repo>` (private). Ветка `main`.
**Без `--force`, без удаления веток.**
