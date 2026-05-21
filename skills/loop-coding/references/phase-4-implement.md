# Phase 4 — Implement

Opus coder subagents execute PLAN-impl.md. Tests from Phase 3 are the contract.

## Spawning coder subagents

Up to 5 concurrent Opus subagents (Orgrimmar limit). Each gets:
- A slice of PLAN-impl.md task list (tasks marked "parallelizable")
- Access to tests/ to know what must pass
- Instruction to commit atomically via `scripts/commit-atomic.sh`

## Subagent prompt template

```
Implement tasks {{TASK_IDS}} from PLAN-impl.md.
Rules:
1. Read tests/ first — those are your contract. Unskip relevant tests.
2. Write minimum code to pass tests. No over-engineering.
3. Follow style: project CLAUDE.md + rules.md + rules/python.md + rules/typescript.md.
4. After each task: bash scripts/test-runner.sh {{LANG}} && bash scripts/commit-atomic.sh "{{message}}"
5. If a test fails after 3 internal attempts, STOP and write BLOCKED-{{TASK_ID}}.md.
6. Do NOT push — orchestrator pushes in Phase 7.
```

## Sequential vs parallel

- Sequential tasks (have dependencies) -> single subagent, ordered
- Parallel tasks (independent) -> up to 5 subagents via parallel Agent calls in one message

Orchestrator (me) decides split based on PLAN-impl.md dependency graph.

## Test enforcement

After each commit:
```bash
bash scripts/test-runner.sh auto  # detects lang from changed files
```

Exit non-zero -> coder subagent must fix before next task. If stuck, writes BLOCKED-*.md and escalates back to orchestrator.

## Guardrails

- No new features beyond PLAN.md.
- No test removal (only unskipping + adding).
- No direct commits to main branch (use feature branch per migration).
- No deletions without explicit authorization in PLAN.md.

## Output

- Feature branch with N atomic commits
- All tests passing locally
- Updated `tests/` (skeletons filled in)
- BLOCKED-*.md files for any unresolved issues
