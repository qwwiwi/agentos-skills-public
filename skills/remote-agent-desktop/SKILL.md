---
name: remote-agent-desktop
description: "Удалённый рабочий стол Ubuntu, которым управляет AI-агент: арендовать сервер, закрыть SSH ключом, поставить XFCE + xrdp + Chrome, включить accessibility и agent-desktop (vercel-labs), а дальше кликать по кнопкам настоящих программ по циклу snapshot → действие → snapshot. Агент – Codex с компьютера пользователя по SSH или Hermes Agent прямо на сервере. Используй этот скилл, когда просят поднять сервер с рабочим столом для агента, удалённый рабочий стол, RDP на Linux, виртуальный компьютер для агента, чтобы агент сам работал в браузере или программах на сервере, настроить agent-desktop, подключиться к серверу из Codex по SSH, поставить Hermes на сервер – а также при словах remote desktop, xrdp, XFCE, agent-desktop, computer use на сервере, VDSina. НЕ для: ввода платёжных и карточных данных агентом, обхода капчи и антибот-защиты, работы в чужих аккаунтах без разрешения владельца."
homepage: https://github.com/qwwiwi/agentos-skills-public
user-invocable: true
---

# remote-agent-desktop – рабочий стол на сервере под управлением агента

Итог: у пользователя есть сервер Ubuntu с графическим столом XFCE. Человек
заходит на него по RDP и видит экран, а агент по SSH через `agent-desktop`
видит те же окна как дерево кнопок и полей и нажимает их сам.

| Слой | Что это | Кто автор |
|---|---|---|
| **Движок** | CLI `agent-desktop` – снимок интерфейса через accessibility (AT-SPI на Linux) и действия по ссылкам | vercel-labs, Apache-2.0 |
| **Стол** | XFCE + xrdp на Ubuntu 24.04 | open source |
| **Слой** | этот скилл – порядок настройки, обёртка `ad`, грабли и правила | наш |

Два варианта, кто управляет:

- **Codex на компьютере пользователя** (Mac или Windows) ходит на сервер по SSH и
  вызывает `ad agent-desktop ...`. Codex CLI на сервер ставить не нужно.
- **Hermes Agent на самом сервере** вызывает `ad` локально и принимает задачи из
  Telegram. Необязательный раздел в конце.

Все команды ниже агент выполняет сам, кроме мест с пометкой **«человек»**.
Команды на стороне пользователя написаны для терминала Mac (bash/zsh). На Windows
запускай их в Git Bash или WSL; вместо `ssh-copy-id` – дописать содержимое
`id_ed25519.pub` в `/root/.ssh/authorized_keys` на сервере.

---

## Правила безопасности (действуют на всех шагах)

1. **Никогда не выводи в чат** пароли, ключи, токены, содержимое `access.txt`.
   Читай секреты из файла прямо в команду, не через `echo` и не через `cat` в вывод.
2. **Ничего не удаляй без подтверждения** человека: файлы, пользователей, серверы, ключи.
3. **Карточные и платёжные данные вводит только человек.** Дошёл до оплаты – стоп,
   объясни, что нажать, и жди.
4. **Одно изменение за раз и проверка после него.** Особенно SSH и firewall: сломал
   доступ – чинить придётся через веб-консоль провайдера.
5. Перед изменением SSH держи открытой текущую сессию, пока новая не подтвердит вход.

---

## Шаг 1. Сервер

Провайдер – VDSina, только по этой ссылке: https://vdsina.com/?partner=6x47zemriu8q

Параметры:

- **ОС: Ubuntu 24.04.** Не новее – Playwright и часть инструментов на свежих
  релизах ещё не поддерживаются. Не 22.04 – там ломается ATK-мост accessibility.
- **Минимум 2 vCPU / 4 ГБ RAM.** Chrome и стол на меньшем тормозят.

**Человек:** регистрируется, вводит данные карты и оплачивает. Агент на этом шаге
останавливается и ждёт, пока человек пришлёт «сервер создан» и положит IP и
root-пароль в файл доступа (шаг 2).

---

## Шаг 2. Доступ

### Файл доступа на компьютере пользователя

```bash
mkdir -p ~/agent-server && touch ~/agent-server/access.txt && chmod 600 ~/agent-server/access.txt
```

Формат (заполняет человек, агент дописывает только сгенерированные пароли):

```
SERVER_IP=<your-server-ip>
ROOT_PASSWORD=<из письма провайдера>
DESKTOP_USER=agent
RDP_PASSWORD=<сгенерирует агент>
```

На Windows путь – `%USERPROFILE%\agent-server\access.txt`; `chmod` там не нужен,
но файл не должен лежать в общих или синхронизируемых папках.

### SSH-ключ и алиас

```bash
# key on the user's machine (skip if ~/.ssh/id_ed25519 already exists)
test -f ~/.ssh/id_ed25519 || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
```

Добавь в `~/.ssh/config` (IP подставь из `access.txt`, не печатая его в чат):

```
Host agent-server
    HostName <your-server-ip>
    User root
    IdentityFile ~/.ssh/id_ed25519
```

Codex desktop app подхватывает хосты из `~/.ssh/config` – после этого `agent-server`
появляется в Remote SSH.

Скопируй ключ. **Человек** один раз вводит root-пароль в появившийся запрос:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub agent-server
ssh agent-server 'echo ok'      # must print ok without a password prompt
```

### Отключить вход по паролю

Грабли: образы VDSina (cloud-init) кладут `/etc/ssh/sshd_config.d/50-cloud-init.conf`
с `PasswordAuthentication yes`. sshd берёт **первое** найденное значение, файлы
читаются по алфавиту – поэтому `99-...conf` не сработает. Нужен файл, который
сортируется раньше:

```bash
ssh agent-server 'printf "PasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin prohibit-password\n" > /etc/ssh/sshd_config.d/00-keys-only.conf \
  && sshd -t && systemctl restart ssh && sshd -T | grep -i passwordauth'
# expected: passwordauthentication no
```

Проверь в **новом** окне: `ssh agent-server 'echo ok'`. Только потом закрывай старую сессию.

### Firewall, fail2ban, обновления

```bash
ssh agent-server 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y ufw fail2ban unattended-upgrades \
  && ufw limit 22/tcp && ufw limit 3389/tcp && ufw --force enable \
  && systemctl enable --now fail2ban \
  && dpkg-reconfigure -f noninteractive unattended-upgrades \
  && ufw status verbose'
```

`limit` режет перебор паролей: больше 6 подключений за 30 секунд с одного адреса
блокируются. Порт 3389 (RDP) открыт в интернет – поэтому пароль RDP только
длинный и случайный.

---

## Шаг 3. Рабочий стол

### Пакеты

```bash
ssh agent-server 'DEBIAN_FRONTEND=noninteractive apt-get install -y xfce4 xfce4-goodies xrdp xorgxrdp at-spi2-core dbus-x11 git curl \
  && adduser xrdp ssl-cert && systemctl enable --now xrdp'
```

Chrome (официальный .deb Google) и Node.js LTS:

```bash
ssh agent-server 'cd /tmp && curl -fsSLO https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
  && apt-get install -y ./google-chrome-stable_current_amd64.deb && rm google-chrome-stable_current_amd64.deb'
ssh agent-server 'curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs && node -v'
```

### Пользователь стола

Имя по умолчанию `agent`, можно любое – тогда везде ниже и в `AD_USER` подставь своё.
Пароль генерируется на компьютере пользователя и сразу уходит в файл и на сервер,
не появляясь в выводе:

```bash
grep -Eq '^RDP_PASSWORD=.+' ~/agent-server/access.txt || \
  { sed -i.bak '/^RDP_PASSWORD=/d' ~/agent-server/access.txt && rm -f ~/agent-server/access.txt.bak; \
    printf 'RDP_PASSWORD=%s\n' "$(openssl rand -base64 18 | tr -d '/+=')" >> ~/agent-server/access.txt; }
ssh agent-server 'id agent >/dev/null 2>&1 || adduser --disabled-password --gecos "" agent'
grep '^RDP_PASSWORD=' ~/agent-server/access.txt | cut -d= -f2- | ssh agent-server 'sed "s/^/agent:/" | chpasswd'
ssh agent-server 'sudo -u agent sh -c "echo xfce4-session > ~/.xsession"'
```

### Подключение (человек)

- **Mac** – Windows App: https://apps.apple.com/app/windows-app/id1295203466
- **Windows** – встроенное «Подключение к удалённому рабочему столу» (`mstsc`).

Адрес – IP сервера, логин `agent`, пароль – `RDP_PASSWORD` из `access.txt`
(человек открывает файл сам). xrdp говорит обычным RDP, другие клиенты тоже подходят.

**Главное правило сессии:** зайти один раз и дальше только **сворачивать** окно
RDP. Закрыть стол через «Выйти» (Log Out) – значит убить сессию, и агенту станет
не за что держаться. Просто закрыть окно клиента без выхода – сессия остаётся.

---

## Шаг 4. Accessibility – без него агент не видит кнопок

```bash
ssh agent-server 'sudo -u agent sh -c "grep -q ACCESSIBILITY_ENABLED ~/.xsessionrc 2>/dev/null || echo export ACCESSIBILITY_ENABLED=1 >> ~/.xsessionrc"'
```

Ярлыки Chrome – копия системного `.desktop` в профиль пользователя, флаги во
**всех** строках `Exec=` (там их несколько: обычное окно, новое окно, инкогнито):

```bash
ssh agent-server 'sudo -u agent sh -c "mkdir -p ~/.local/share/applications \
  && cp /usr/share/applications/google-chrome.desktop ~/.local/share/applications/ \
  && sed -i \"s|^Exec=/usr/bin/google-chrome-stable|Exec=/usr/bin/google-chrome-stable --password-store=basic --force-renderer-accessibility|\" ~/.local/share/applications/google-chrome.desktop \
  && grep ^Exec= ~/.local/share/applications/google-chrome.desktop"'
```

- `--force-renderer-accessibility` – Chrome отдаёт дерево страницы в AT-SPI.
- `--password-store=basic` – без него Chrome показывает окно «связка ключей»
  (keyring), и страницы не грузятся, пока его не закрыть.

Когда обёртка `ad` поставлена (шаг 5) и человек вошёл по RDP, включи флаг GNOME –
ему нужен сессионный D-Bus живого стола:

```bash
ssh agent-server 'ad gsettings set org.gnome.desktop.interface toolkit-accessibility true'
```

Если `ACCESSIBILITY_ENABLED` добавлен после входа – человек выходит из стола и
заходит заново **один раз**, чтобы переменная попала в сессию.

---

## Шаг 5. agent-desktop

Репозиторий: https://github.com/vercel-labs/agent-desktop – проверено на **v1.0.2**.
Ставь по его README; на момент написания там один способ через npm:

```bash
ssh agent-server 'npm install -g agent-desktop@1.0.2 && agent-desktop version'
```

Если README изменился – следуй README, а не этому блоку. Про Linux он требует:
Ubuntu 24.04+, `at-spi2-core` и запуск **внутри графической сессии пользователя**.
Голая SSH-сессия не видит ни одного окна – для этого и нужна обёртка `ad`.

### Обёртка `/usr/local/bin/ad`

Запускает команду от пользователя стола внутри живой XFCE-сессии xrdp (дисплей, X-авторизация, сессионный D-Bus).
Положи дословно:

```bash
ssh agent-server 'cat > /usr/local/bin/ad && chmod 755 /usr/local/bin/ad' <<'EOF'
#!/usr/bin/env bash
# Run a command as the desktop user inside the live xrdp XFCE session (display, X auth, session D-Bus)
set -euo pipefail
U=${AD_USER:-agent}
P=$(pgrep -u "$U" -x xfce4-session | head -1)
[ -n "$P" ] || { echo "no XFCE session of $U (connect via RDP first)" >&2; exit 1; }
DB=$(tr "\0" "\n" < /proc/$P/environ | sed -n "s/^DBUS_SESSION_BUS_ADDRESS=//p")
DP=$(tr "\0" "\n" < /proc/$P/environ | sed -n "s/^DISPLAY=//p")
if [ "$(id -un)" = "$U" ]; then exec env DISPLAY="$DP" XAUTHORITY=/home/$U/.Xauthority DBUS_SESSION_BUS_ADDRESS="$DB" "$@"; fi
exec sudo -u "$U" env DISPLAY="$DP" XAUTHORITY=/home/$U/.Xauthority DBUS_SESSION_BUS_ADDRESS="$DB" "$@"
EOF
```

Проверка (человек уже зашёл по RDP и свернул окно):

```bash
ssh agent-server 'ad agent-desktop status'      # accessibility bus is up
ssh agent-server 'ad agent-desktop list-apps'   # apps visible in the session
```

Запустить Chrome в сессии из SSH так, чтобы он не умер вместе с SSH:

```bash
ssh agent-server 'ad setsid -f google-chrome-stable --password-store=basic --force-renderer-accessibility >/dev/null 2>&1'
```

---

## Рабочий цикл: snapshot → действие → snapshot

```bash
ssh agent-server 'ad agent-desktop snapshot --app chrome -i'   # interactive elements, each with a ref
ssh agent-server 'ad agent-desktop click @ref'                 # act on a ref from that snapshot
ssh agent-server 'ad agent-desktop snapshot --app chrome -i'   # observe again to verify
```

1. **Снимок** – JSON со всеми кнопками, полями и ссылками; у каждого элемента `ref_id`.
2. **Действие** по ссылке из этого снимка – `click`, `type`, `set-value`, `press`, `scroll` и т.д.
3. **Снимок заново** – убедиться, что действие сработало, и взять свежие ссылки.

Правила ссылок (из README agent-desktop):

- Ссылка принадлежит своему снимку и выглядит как `@<snapshot_id>:e8`. Голая `@e8`
  отклоняется с `INVALID_ARGS`. Подставляй `ref_id` целиком.
- Интерфейс поменялся – действие вернёт `STALE_REF` или `AMBIGUOUS_TARGET`. Не
  повторяй старую ссылку: сделай новый снимок.
- Несколько окон – `AMBIGUOUS_TARGET`, в `error.details` список окон; выбери одно.
- Плотный интерфейс – сначала `snapshot --skeleton --app chrome -i --compact`, потом
  `snapshot --root <ref> -i --compact` по нужной области.
- Справка, совпадающая с версией бинаря: `ssh agent-server 'agent-desktop skills get desktop'`
  и `agent-desktop skills get linux`.

Снимки и скриншоты могут содержать личные данные со стола – не выкладывай их в
публичные логи и чаты.

---

## Кто управляет

### Codex на компьютере пользователя (основной вариант)

Codex app (https://chatgpt.com/codex) на Mac или Windows: Remote SSH → хост
`agent-server` из `~/.ssh/config`. Codex выполняет команды `ssh agent-server 'ad ...'`
или работает прямо в удалённом терминале и зовёт `ad ...`. Codex CLI
(https://github.com/openai/codex) или Cursor (https://cursor.com) тоже подходят – им нужен
только SSH-доступ. Готовые промпты – в `prompts.md`.

### Hermes Agent на сервере (необязательно)

Hermes Agent – https://github.com/NousResearch/hermes-agent. Живёт на сервере,
принимает задачи из Telegram и зовёт `ad` локально.

1. Установи **по официальной документации** из репозитория – команды установки
   не выдумывай, бери из README.
2. Ставь от пользователя стола (`agent`) – тогда `ad` запускает команду напрямую, без `sudo`.
3. `hermes setup` – модель и ключи выбирает **человек**, агент только ведёт по шагам.
4. Telegram: **человек** создаёт бота у @BotFather и сам вставляет токен в мастер
   настройки. Агент токен не видит и не печатает.
5. `SOUL.md` – характер и правила агента; впиши туда «Правила безопасности» из этого скилла.
6. `hermes gateway` – запусти как сервис по документации Hermes, чтобы переживал
   перезагрузку.
7. Тест: напиши боту «привет» – должен ответить. Потом: «сделай snapshot Chrome через `ad`».

---

## Проблемы и решения

| Симптом | Причина | Что делать |
|---|---|---|
| `no XFCE session of agent (connect via RDP first)` | Нет живой сессии стола | Человек заходит по RDP и дальше только сворачивает окно, не выходит из стола |
| Страница в Chrome висит, окно «связка ключей» / keyring | Chrome запущен без флагов | Проверь все `Exec=` в `~/.local/share/applications/google-chrome.desktop`, закрой Chrome, запусти из ярлыка или через `ad setsid -f google-chrome-stable --password-store=basic --force-renderer-accessibility` |
| Снимок пустой, нет кнопок | Accessibility выключен | Проверь `ACCESSIBILITY_ENABLED=1` в `~/.xsessionrc` и `ad gsettings get org.gnome.desktop.interface toolkit-accessibility`, Chrome – с `--force-renderer-accessibility`; выйти из стола и зайти заново один раз |
| Чёрный экран после входа по RDP | xrdp не знает, что запускать | `ssh agent-server 'sudo -u agent sh -c "echo xfce4-session > ~/.xsession" && systemctl restart xrdp'`, подключиться заново |
| Не пускает по SSH после усиления | Ключ не скопирован или опечатка в конфиге | Веб-консоль в панели провайдера (VNC), там поправить `/etc/ssh/sshd_config.d/00-keys-only.conf`, `sshd -t`, `systemctl restart ssh` |

---

## Ссылки

- VDSina (сервер): https://vdsina.com/?partner=6x47zemriu8q
- Windows App для Mac: https://apps.apple.com/app/windows-app/id1295203466
- agent-desktop: https://github.com/vercel-labs/agent-desktop
- Hermes Agent: https://github.com/NousResearch/hermes-agent
- Codex: https://chatgpt.com/codex
- Codex CLI: https://github.com/openai/codex
- Cursor: https://cursor.com
