# Phase 5 — Review

Codex and Opus review the diff independently.

## Subagents

| ID | Model | Focus |
|---|---|---|
| A | Codex (`codex review` CLI) | security, architecture alignment, corner cases, performance |
| B | Opus subagent (code-reviewer) | readability, consistency, patterns, test quality |

## Invocation

```bash
bash scripts/parallel-review.sh review "$RUN_DIR"
```

This script:
1. Computes diff: `git diff $BASE..HEAD`
2. Launches Codex review via `codex exec "review these changes: {{DIFF}}"`
3. Launches Opus code-reviewer subagent with same diff
4. Collects both outputs to `review-codex.md` and `review-opus.md`
5. Runs `scripts/merge-reviews.sh` -> `REVIEW.md`

## Severity taxonomy

| Severity | Definition | Action |
|---|---|---|
| critical | Security hole, data loss risk, breaks prod | BLOCK — must fix before merge |
| high | Wrong architecture, missing tests for main paths, perf regression | BLOCK — must fix |
| medium | Style violation, missed edge case, suboptimal pattern | Fix if cheap; can defer with justification |
| low | Nit, minor improvement | Optional |

## REVIEW.md structure

```markdown
# REVIEW.md

## Consensus (both models)
### Critical
...
### High
...
### Medium
...

## Divergent (one model only)
### Codex raised
...
### Opus raised
...

## Test expansion
Security tests to add: ...
Performance tests to add: ...
Edge case tests to add: ...
```

## Test expansion

Review phase adds tests for:
- Security findings (e.g., auth bypass -> add test)
- Performance issues (e.g., N+1 query -> add perf test)
- Edge cases discovered

Write these as unskipped tests in `tests/` before entering Phase 6.

## Handoff to Phase 6

If any critical/high remain -> Phase 6 fix-loop.
If only medium/low remain -> prince decides defer vs fix.
If none -> skip to Phase 7.
