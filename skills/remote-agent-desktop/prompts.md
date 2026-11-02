# Готовые промпты

Два сообщения для агента (Codex app, Codex CLI или Cursor на компьютере пользователя).
Копируй целиком. Скилл `remote-agent-desktop` должен быть установлен.

---

## Промпт 1. Поднять сервер с рабочим столом

```
Используй скилл remote-agent-desktop. Подними мне удалённый рабочий стол Ubuntu для агента.

1. Сервер: VDSina строго по ссылке https://vdsina.com/?partner=6x47zemriu8q, Ubuntu 24.04 (не новее), минимум 2 vCPU / 4 ГБ RAM. Регистрацию, данные карты и оплату делаю я сам – дойдёшь до оплаты, остановись и скажи, что нажать.
2. Доступы храни в ~/agent-server/access.txt (chmod 600). IP и root-пароль я положу туда сам. Никогда не выводи пароли, ключи и токены в чат.
3. SSH: ключ с моего компьютера, алиас agent-server в ~/.ssh/config, вход по паролю выключи файлом /etc/ssh/sshd_config.d/00-keys-only.conf (он должен быть раньше 50-cloud-init.conf) и проверь через sshd -T | grep passwordauth. Перед закрытием старой сессии проверь вход в новой.
4. ufw limit 22/tcp и 3389/tcp, fail2ban, unattended-upgrades.
5. Стол: пользователь agent со случайным паролем для RDP (сразу в access.txt, не в чат), xfce4, xrdp, xorgxrdp, at-spi2-core, google-chrome-stable, git, Node.js LTS.
6. Accessibility: ACCESSIBILITY_ENABLED=1 в ~/.xsessionrc пользователя agent, ярлык Chrome с --password-store=basic --force-renderer-accessibility во всех строках Exec=.
7. agent-desktop по README https://github.com/vercel-labs/agent-desktop и обёртка /usr/local/bin/ad из скилла.

Делай по одному шагу и проверяй каждый. Ничего не удаляй без моего подтверждения. В конце скажи, как мне подключиться по RDP с моего компьютера (Mac – Windows App, Windows – «Подключение к удалённому рабочему столу»), и попроси зайти один раз и свернуть окно.
```

---

## Промпт 2. Управлять рабочим столом

```
Используй скилл remote-agent-desktop. Я зашёл на рабочий стол сервера agent-server по RDP и свернул окно – сессия живая, не выходи из неё.

1. Проверь: ssh agent-server 'ad agent-desktop status' и включи ad gsettings set org.gnome.desktop.interface toolkit-accessibility true.
2. Запусти Chrome в сессии с флагами --password-store=basic --force-renderer-accessibility.
3. Задача: <что сделать в браузере, например «открой сайт example.com и найди раздел контактов»>.

Работай циклом: ssh agent-server 'ad agent-desktop snapshot --app chrome -i' → действие по ref из этого снимка (ssh agent-server 'ad agent-desktop click @ref') → снова snapshot, чтобы проверить результат. Старые ref после изменения страницы не используй.

Не вводи данные карт и платежей, не печатай пароли и токены, ничего не удаляй без моего подтверждения. Если снимок пустой или кнопок нет – смотри таблицу «Проблемы и решения» в скилле. В конце коротко расскажи, что сделал и что увидел на экране.
```
