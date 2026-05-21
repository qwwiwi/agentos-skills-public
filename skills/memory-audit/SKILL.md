---
name: memory-audit
description: >
  Самоаудит памяти и состояния агента. Используй когда: (1) user пишет
  «аудит памяти», «проверь память», «memory-audit», (2) после крупных изменений.
  Проверяет: memory backend, личную память, скиллы, cron, heartbeat.
---

# Memory Audit -- Самоаудит (memory backend V2)

> **DEPRECATED 2026-05-17 — memory backend cutover.** Этот скилл построен на your memory backend (your-memory-cli). После hard cutover на gbrain MCP координация переехала в `dashi-gbrain-{tasks,swarm,memory,recall}` MCP. Используй MCP tools вместо команд из этого файла. Полный rewrite/удаление — в отдельном wave (см. task #7 staging server). Если ты попал сюда автоматически по триггеру — игнорируй тело и иди в `dashi-gbrain-tasks.task_list()` / `dashi-gbrain-swarm.list_my_pending()`.

Проверяй факты через shell-команды. Не полагайся на допущения.

---

## Раздел А: memory backend -- единый источник правды

```bash
echo "=== memory backend connectivity ==="
# Check memory system health && echo "OK memory backend" || echo "FAIL memory backend"

echo ""
echo "=== Inbox ==="
# Check inbox via your memory system | python3 -c "
import json, sys
data = json.load(sys.stdin)
if isinstance(data, dict):
    print(f'{len(data)} сообщений в inbox')
else:
    print('inbox пуст или ошибка')" 2>/dev/null

echo ""
echo "=== My tasks ==="
# List tasks via your task system | python3 -c "
import json, sys
tasks = json.load(sys.stdin)
active = [(t.get('status','?'), t.get('title','?'))
          for t in tasks.values()
          if isinstance(t, dict) and t.get('assignee') == 'your-coordinator'
          and t.get('status') not in ('done', None)]
print(f'{len(active)} активных задач')
for s, title in active[:5]:
    print(f'  [{s}] {title}')" 2>/dev/null

echo ""
echo "=== Agent status ==="
# Get agent status via your memory system | python3 -c "
import json, sys
a = json.load(sys.stdin)
print(f'Status: {a.get(\"status\", \"?\")}')
print(f'LastSeen: {a.get(\"lastSeen\", \"?\")}')
print(f'Heartbeat: {a.get(\"heartbeat\", \"?\")}')" 2>/dev/null
```

---

## Раздел Б: Личная память (локальная)

```bash
WS="~/.claude"
echo "=== Local memory files ==="
for f in \
  "$WS/MEMORY.md" \
  "$WS/SOUL.md" \
  "$WS/memory/hot/HOT_MEMORY.md" \
  "$WS/memory/warm/WARM_MEMORY.md" \
  "$WS/memory/warm/WATCHLIST.md" \
  "$WS/memory/warm/LEARNINGS.md"
do
  if [ -f "$f" ]; then
    SIZE=$(wc -c < "$f")
    echo "OK $(basename $f) -- ${SIZE} bytes"
    [ "$SIZE" -gt 8192 ] && echo "  WARN: >8KB, approaching rotation"
    [ "$SIZE" -gt 10240 ] && echo "  CRITICAL: >10KB, flush blocked!"
  else
    echo "MISSING: $f"
  fi
done

echo ""
echo "=== memory backend memory files ==="
for f in "$WS/firebase-mirror/"*.md; do
  [ -f "$f" ] && echo "OK $(basename $f)" || echo "MISSING firebase memory"
done
```

---

## Раздел В: Скиллы -- актуальность

```bash
echo "=== Skills referencing deprecated paths ==="
grep -rl "shared-dark-lady\|agent-memory/shared" \
  "~/.claude/skills/" 2>/dev/null \
  | grep -v ".backup" \
  | while read f; do echo "WARN: deprecated path in $f"; done

echo ""
echo "=== Key skills check ==="
for skill in shared-memory firebase-ops claude-code-bridge task-system; do
  F="~/.claude/skills/$skill/SKILL.md"
  if [ -f "$F" ]; then
    if grep -q "your-memory-cli" "$F"; then
      echo "OK $skill (uses your-memory-cli)"
    else
      echo "WARN $skill (no your-memory-cli reference -- outdated?)"
    fi
  else
    echo "MISSING: $skill"
  fi
done
```

---

## Раздел Г: Obsidian sync и cron

```bash
echo "=== Cron jobs ==="
crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$"

echo ""
echo "=== Obsidian sync ==="
SYNC="$HOME/scripts/firebase-to-obsidian.sh"
[ -f "$SYNC" ] && echo "OK sync script exists" || echo "MISSING sync script"

HC="$HOME/scripts/firebase-obsidian-healthcheck.sh"
[ -f "$HC" ] && echo "OK healthcheck exists" || echo "MISSING healthcheck"

LOG="$HOME/.logs/obsidian-sync.log"
if [ -f "$LOG" ]; then
  LAST=$(tail -1 "$LOG")
  echo "Last sync: $LAST"
else
  echo "WARN: no sync log"
fi

echo ""
echo "=== Obsidian vault ==="
VAULT="$HOME/Obsidian/<your-vault>"
[ -d "$VAULT/Agents" ] && echo "OK Agents/" || echo "MISSING Agents/"
[ -d "$VAULT/Tasks" ] && echo "OK Tasks/" || echo "MISSING Tasks/"
[ -d "$VAULT/Projects" ] && echo "OK Projects/" || echo "MISSING Projects/"
[ -d "$VAULT/Reference/Backups" ] && echo "OK Backups/" || echo "MISSING Backups/"
```

---

## Раздел Д: Heartbeat

```bash
echo "=== Update heartbeat ==="
# Update heartbeat via your memory system \
  '{"lastSeen":"'"$(date -Iseconds)"'","status":"online"}' \
  && echo "OK heartbeat updated" || echo "FAIL heartbeat"
```

---

## Финальный отчёт

После выполнения всех проверок составь отчёт:

```markdown
# Memory Audit Report -- your-coordinator -- YYYY-MM-DD

| Раздел | Статус | Детали |
|--------|--------|--------|
| A. memory backend | OK/WARN/FAIL | connectivity, inbox, tasks |
| Б. Личная память | OK/WARN/FAIL | files, sizes |
| В. Скиллы | OK/WARN | deprecated paths |
| Г. Obsidian sync | OK/WARN/FAIL | cron, vault |
| Д. Heartbeat | OK/FAIL | last update |
```

Если найдены CRITICAL -- сообщи user немедленно.
