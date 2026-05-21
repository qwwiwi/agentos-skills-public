# Phase 6 — Fix-loop

Max 3 iterations. Else escalate.

## Controller

```bash
bash scripts/loop-controller.sh "$RUN_DIR"
```

State: `$RUN_DIR/.iteration-count` (starts at 0).

## Per-iteration flow

1. Read REVIEW.md; filter critical + high.
2. If empty -> exit loop (success).
3. Read `.iteration-count`. If >= 3 -> `scripts/escalate.sh "$RUN_DIR"` and exit.
4. Spawn Opus coder subagent with REVIEW.md as context:

```
Fix the following findings from REVIEW.md:
{{CRITICAL + HIGH issues}}
Rules:
- Minimum change to address root cause (not symptom)
- Tests must still pass after each fix
- Commit atomically per fix
- Update FIX-LOG.md with: what, why, before/after
```

5. After subagent completes:
   - `scripts/test-runner.sh auto` must pass
   - `scripts/parallel-review.sh review` runs again -> new REVIEW.md
6. Increment `.iteration-count`. GOTO 1.

## FIX-LOG.md format

```markdown
## Iteration 1 (2026-04-17 14:30)
Fixed:
- [critical] Auth bypass in /api/mcp — added permission check before key fetch
- [high] Missing test for expired token — added in tests/auth_test.py

Remaining from iteration 1 review:
- [high] Race condition in webhook handler

## Iteration 2 (2026-04-17 15:10)
...
```

## Escalation at iteration 3

`scripts/escalate.sh "$RUN_DIR"` sends to prince:
- REVIEW.md (current state)
- FIX-LOG.md (what we tried)
- DIFF-SUMMARY.md (what changed across iterations)

Caption template:
```
loop-coding: итерация 3/3 не сошлась по задаче {{TASK_SLUG}}.
Остались: N critical, M high.
Артефакты в attachment. Нужна твоя оценка.
```

Then HALT. Do not start iteration 4.
