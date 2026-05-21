# DEPLOY.md

Task: {{TASK_SLUG}}
Started: {{DATE_UTC}}

## Pre-checks

- tests: pending/green/failed
- REVIEW.md: pending/clean/has-critical
- branch: {{BRANCH}}, rebased onto {{BASE}}
- secrets: gitignored check

## Git push

- pushed: {{BRANCH}} -> origin
- commit: {{SHA}} (head)

## Staging

- timestamp: ...
- backup: restic snapshot {{ID}}
- deploy.sh exit: ...
- health: ... (url: ...)
- screenshot: ...

## Production

- status: not-started / awaiting-approval / approved / deployed / failed
- requested: ...
- approved: ...
- deployed: ...
