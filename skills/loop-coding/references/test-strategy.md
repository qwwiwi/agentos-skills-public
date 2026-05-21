# Test Strategy (per language)

TDD-adapted for AI: skeletons in Plan, extend in Review.

## Phase placement

| Phase | Test activity |
|---|---|
| 1 Research | Identify test framework(s) for the stack — no code |
| 2 Audit | Inventory existing tests + coverage gaps — no code |
| 3 Plan | Write test SKELETONS (TDD contracts) for every interface |
| 4 Implement | Unskip + implement; run after every commit |
| 5 Review | Add security / perf / edge-case tests |
| 6 Fix-loop | Add regression test for each fix |
| 7 Ship | Full suite green = precondition to deploy |

## Python (backend)

Framework: pytest + pytest-asyncio.

| Type | Marker | Lives in |
|---|---|---|
| Unit | (none) | `tests/unit/test_*.py` |
| Integration | `@pytest.mark.integration` | `tests/integration/test_*.py` |
| Contract | `@pytest.mark.contract` | `tests/contract/test_*.py` |
| E2E | `@pytest.mark.e2e` | `tests/e2e/test_*.py` |
| Security | `@pytest.mark.security` | `tests/security/test_*.py` |

Reference style: `qwwiwi/architecture-brain-tests` (760 tests, structured under `tests/` mirroring source).

Run:
```bash
pytest -m "not e2e"         # fast
pytest -m integration       # infra required
pytest --cov=. --cov-fail-under=80  # coverage gate
```

## TypeScript / frontend

Framework: Vitest (unit + component), Playwright (E2E), Biome (lint).

| Type | File pattern | Runner |
|---|---|---|
| Unit | `src/**/*.test.ts` | Vitest |
| Component | `src/**/*.test.tsx` | Vitest + @testing-library/react |
| Snapshot | `src/**/*.snap` | Vitest |
| E2E | `e2e/**/*.spec.ts` | Playwright |

Biome replaces ESLint + Prettier but does NOT run tests. Keep biome for lint/format, use Vitest for logic, Playwright for browser.

Run:
```bash
pnpm test               # vitest run
pnpm test:e2e           # playwright
pnpm biome check .      # lint
```

## Bash

Framework: bats-core.

```bash
# tests/bats/my-script.bats
@test "foo returns 0" {
  run bash scripts/foo.sh
  [ "$status" -eq 0 ]
}
```

Run: `bats tests/bats/`.

## Go (if encountered)

Standard `go test` + `testify` for assertions. Table-driven tests preferred.

## Coverage gates

Minimum to merge (unless PLAN.md overrides):
- Python: 80% line
- TypeScript: 70% line (front-end harder to cover)
- Bash scripts: smoke tests only (1 test per script minimum)

## Seeded patterns

`scripts/scaffold-tests.sh {{lang}} {{module}}` generates test skeletons from PLAN-arch.md interfaces.
