#!/usr/bin/env bash
set -euo pipefail

# Robust launcher for Telegram session generation.
# Works from the skill folder and reuses workspace-level .venv.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

cd "$SCRIPT_DIR"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  python3 -m venv "$VENV_DIR"
fi

"${VENV_DIR}/bin/pip" install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "=== Генерация Telegram Session String ==="
echo ""
echo "Вам нужно будет ввести:"
echo "1) Номер телефона (+<код_страны><номер>)"
echo "2) Код подтверждения из Telegram"
echo "3) Пароль 2FA (если включен)"
echo ""

"${VENV_DIR}/bin/python" session_string_generator.py

echo ""
echo "=== Готово ==="
echo "Проверьте session string:"
grep '^TELEGRAM_SESSION_STRING=' .env || true
