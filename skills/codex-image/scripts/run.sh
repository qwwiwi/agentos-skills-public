#!/usr/bin/env bash
# Self-contained launcher for codex_image.py — bootstraps the skill's own venv.
# Usage: run.sh "prompt in English" [quality:low|medium|high] [aspect:landscape|square|portrait]
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$SKILL_DIR/.venv"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[codex-image] bootstrapping venv at $VENV" >&2
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade openai
fi

exec "$VENV/bin/python" "$SKILL_DIR/scripts/codex_image.py" "$@"
