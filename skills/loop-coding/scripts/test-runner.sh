#!/usr/bin/env bash
# Usage: test-runner.sh <lang|auto>
# Runs tests appropriate for the language. Exit 0 on success, non-zero on failure.
# Does NOT run linters — keep linting in a separate pipeline step.
set -euo pipefail

LANG="${1:-auto}"

if [[ "$LANG" == "auto" ]]; then
  # Explicit precedence: python > typescript > bash (parenthesized for bash operator precedence)
  if [[ -f "pytest.ini" || -f "pyproject.toml" ]] || { [[ -d "tests" ]] && [[ -n "$(find . -maxdepth 3 -name "conftest.py" -print -quit 2>/dev/null)" ]]; }; then
    LANG=python
  elif [[ -f "package.json" ]]; then
    LANG=typescript
  elif [[ -d "tests/bats" ]]; then
    LANG=bash
  else
    echo "cannot auto-detect language" >&2
    exit 1
  fi
fi

case "$LANG" in
  python)
    pytest -q --tb=short
    ;;
  typescript|ts)
    if command -v pnpm >/dev/null 2>&1 && [[ -f "pnpm-lock.yaml" ]]; then
      pnpm test
    elif command -v bun >/dev/null 2>&1 && [[ -f "bun.lock" ]]; then
      bun test
    else
      npm test
    fi
    ;;
  bash)
    bats tests/bats/
    ;;
  *)
    echo "unsupported language: $LANG" >&2
    exit 1
    ;;
esac
