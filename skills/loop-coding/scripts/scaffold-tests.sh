#!/usr/bin/env bash
# Usage: scaffold-tests.sh <lang:python|typescript|bash> <module-name> [<run-dir>]
# Generates a minimal test skeleton for the given module.
set -euo pipefail
LANG="${1:?lang required}"
MODULE="${2:?module name required}"
RUN_DIR="${3:-}"

TESTS_DIR="tests"
[[ -n "$RUN_DIR" && -d "$RUN_DIR/tests" ]] && TESTS_DIR="$RUN_DIR/tests"

mkdir -p "$TESTS_DIR"
SAFE=$(printf '%s' "$MODULE" | tr -cd 'A-Za-z0-9_')

case "$LANG" in
  python)
    FILE="$TESTS_DIR/test_${SAFE}.py"
    cat > "$FILE" <<PY
# Test skeleton for $MODULE (generated $(date -u +%FT%TZ))
import pytest

def test_${SAFE}_smoke():
    # TODO: implement
    pytest.skip("skeleton")
PY
    ;;
  typescript|ts)
    FILE="$TESTS_DIR/${SAFE}.test.ts"
    cat > "$FILE" <<TS
// Test skeleton for $MODULE (generated $(date -u +%FT%TZ))
import { describe, it } from 'vitest';

describe('$MODULE', () => {
  it.todo('smoke');
});
TS
    ;;
  bash)
    FILE="$TESTS_DIR/${SAFE}.bats"
    cat > "$FILE" <<BATS
#!/usr/bin/env bats
# Test skeleton for $MODULE (generated $(date -u +%FT%TZ))

@test "smoke" {
  skip "skeleton"
}
BATS
    ;;
  *)
    echo "unknown lang: $LANG" >&2
    exit 1
    ;;
esac

echo "scaffolded -> $FILE"
