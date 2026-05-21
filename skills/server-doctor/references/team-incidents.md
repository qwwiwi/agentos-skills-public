# Team Incident Playbook

Дополнение к `openclaw-incident-response.md` -- наши реальные сценарии.

## 1. Повреждённая сессия (tool_use без tool_result)

**Симптом:** Агент отвечает ошибкой `tool_use ids were found without tool_result blocks immediately after`.

**Причина:** LLM вызвал tool_use, но tool_result не вернулся (таймаут, краш, потеря данных). Сессия сохранена на диск с битым state.

**Диагностика:**
```bash
# Найти активные сессии агента
ls -la ~/.openclaw/agents/main/sessions/*.jsonl

# Найти сессию для конкретного пользователя
grep -l "USER_ID" ~/.openclaw/agents/main/sessions/*.jsonl

# Проверить последние записи
tail -3 SESSION_FILE | python3 -c "import sys,json; [print(json.dumps(json.loads(l))[:200]) for l in sys.stdin if l.strip()]"
```

**Починка:**
```bash
# Переименовать повреждённую сессию
mv SESSION_FILE SESSION_FILE.corrupted.bak

# Перезапустить gateway
kill $(pgrep -u USERNAME -f "openclaw-gateway")
sleep 2
su - USERNAME -c "nohup openclaw gateway start > /dev/null 2>&1 &"
```

**Важно:** Просто перезапуск gateway НЕ помогает -- сессия загружается с диска обратно.

## 2. Два gateway-процесса на одном хосте

**Симптом:** Агент не обрабатывает сообщения. В `ps aux` два процесса openclaw-gateway.

**Причина:** Разные пользователи запустили gateway (например `openclaw` и `batrak`).

**Диагностика:**
```bash
ps aux | grep openclaw-gateway | grep -v grep
```

**Починка:**
```bash
# Убить лишний процесс
kill PID_OF_EXTRA_PROCESS

# Убедиться что остался только один
ps aux | grep openclaw-gateway | grep -v grep
```

## 3. Порт занят (Address already in use)

**Симптом:** `edgelab-api.service` не стартует. `[Errno 98] Address already in use`.

**Диагностика:**
```bash
fuser 8090/tcp
ss -tulpn | grep 8090
```

**Починка:**
```bash
fuser -k 8090/tcp
systemctl restart edgelab-api
```

## 4. Coordination backend недоступен

**Симптом:** обращение к coordination layer (`get`/`list`) возвращает ошибку или пустоту.

**Диагностика:**
```bash
# check agent status via your task system 2>&1
curl -s "https://<your-firebase-url>/.json?shallow=true" 2>&1 | head -20
```

**Workaround:** Работать по локальной памяти (HOT/WARM_MEMORY.md) с пометкой [unverified].

## 5. Chromium headless зависает

**Симптом:** CDP команды не выполняются, порт 9222 не отвечает.

**Диагностика:**
```bash
curl -s http://localhost:9222/json/version
pgrep -f chromium
```

**Починка:**
```bash
pkill -f chromium
sleep 2
bash ~/.claude/skills/chromium/scripts/chromium-launch.sh
```

## 6. SSE listener отвалился

**Симптом:** firebase-mirror/ не обновляется.

**Диагностика:**
```bash
pgrep -f firebase-sse
ls -la ~/.claude/firebase-mirror/ | head -5
```

**Починка:**
```bash
pkill -f firebase-sse
nohup bash ~/scripts/firebase-sse-listener.sh &
```
