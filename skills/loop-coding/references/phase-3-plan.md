# Phase 3 — Plan + Test Skeletons

Codex GPT-5.5 writes BOTH the architectural plan and the implementation plan. Opus is reserved for test-skeleton scaffolding only (after Codex plan is done). Single-critic phase (Opus removed from planning 2026-04-24 to offload subscription — see core/rules.md "Model role split").

## Subagents

| ID | Model | Output |
|---|---|---|
| A | Codex GPT-5.5 | `PLAN.md` — arch + impl together: interfaces, contracts, module boundaries, ordered task list, file-level changes, commit strategy, milestones, rollback plan |
| B | Opus subagent | `tests/` — TDD skeletons for each contract (runs AFTER Codex plan lands; consumes PLAN.md) |

## Codex plan prompt

```bash
codex exec --skip-git-repo-check "Based on RESEARCH.md and AUDIT.md, design the FULL plan for {{TASK}}.
Output PLAN.md with TWO parts:

## Part 1 — Architecture
- Module boundaries and responsibilities
- Public interfaces (types, signatures)
- Data contracts (schemas)
- Integration points
- Migration sequence (what moves when)
- Rollback points

## Part 2 — Implementation
- Ordered task list (30-50 atomic tasks)
- File-level changes for each task
- Commit strategy (atomic, each commit passing tests)
- Dependencies between tasks
- Parallelization opportunities (which tasks can run in parallel coder subagents)
- Milestones (5-7 checkpoint commits)
- Estimated model per task (default Opus coder)

Be exhaustive — Opus subagents will execute this without re-planning."
```

## Opus test skeleton prompt (post-Codex)

```
Given PLAN.md (Codex-authored), generate test skeletons under tests/.
Style reference: qwwiwi/architecture-brain-tests.
For each public interface in PLAN.md Part 1 (Architecture):
- Unit test skeleton (happy path + edge cases) — marked @pytest.mark.skip for now
- Integration test skeleton for module boundaries
- Contract test for data schemas
Include docstrings that describe what must be true, not how to test it yet.
```

Python: pytest + pytest-asyncio.
TypeScript: Vitest (+ Playwright for E2E). Biome handles linting but not testing.
Bash: bats-core for script tests.

## Output

`PLAN.md` is the single source of truth (no merge step — Codex writes both halves directly).

## Validation

Before proceeding to Phase 4:
- All tests in `tests/` compile / parse (even though skipped)
- `scripts/plan-lint.sh $RUN_DIR` passes
- Prince review optional but recommended for high-risk migrations (auto-flag if rollback cost is high)
