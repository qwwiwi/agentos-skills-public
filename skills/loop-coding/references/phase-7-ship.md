# Phase 7 — Ship

Git push autonomous. Staging autonomous. Production requires prince OK.

## Pre-ship checks

`scripts/pre-ship.sh "$RUN_DIR"` verifies:
- All tests green
- REVIEW.md has no critical/high
- Branch is up to date with main (rebase if not)
- No uncommitted changes
- .env and secrets are gitignored

If any check fails -> abort Phase 7 with clear error.

## Git push (autonomous)

```bash
bash scripts/commit-atomic.sh --push "merge complete for {{TASK_SLUG}}"
```

- Push to feature branch on origin (no --force)
- If repo configured in `mapping-repositories`, also tag the push
- No PR auto-creation unless PLAN.md specifies it

## Deploy decision tree

```
has deploy.sh?
├── no  -> log "no deploy.sh, skipping" to DEPLOY.md; end
└── yes -> project has users in prod?
    ├── no  (staging-only project) -> deploy staging; log; end
    └── yes -> deploy staging; verify; REQUEST PRINCE OK for prod
```

Project "has users" heuristic:
- `<your-domain>`, `<your-domain>`, main `edgelab` platform -> yes
- `*-staging`, experimental repos, `my-*`, fresh repos -> no
- If uncertain -> treat as YES (safer default)

## Staging deploy

```bash
bash scripts/deploy-helper.sh staging "$RUN_DIR"
```

Wraps project `scripts/deploy.sh staging`:
1. DO Spaces backup via restic (mandatory before any deploy)
2. Run `./scripts/deploy.sh staging`
3. Post-deploy verification:
   - `curl -fsS $STAGING_URL/health` returns 200
   - If frontend: agent-browser screenshot + visual check
4. Log all output to DEPLOY.md

## Production deploy

NEVER autonomous. Flow:
1. After staging deploy succeeds, orchestrator sends to Telegram:

```
loop-coding: staging deploy OK для {{TASK_SLUG}}.
URL: {{STAGING_URL}}
Проверено: tests green, health check 200, screenshot attached.
Разрешить prod deploy? (ответь "да, на prod")
```

2. WAIT for explicit "да, на prod" / "ок, на прод" / equivalent.
3. If received within session -> `scripts/deploy-helper.sh production "$RUN_DIR"`.
4. If session ends without approval -> DEPLOY.md records "awaiting prod approval".

## DEPLOY.md format

```markdown
# DEPLOY.md

## Pre-checks (2026-04-17 15:30)
- tests: green
- REVIEW.md: clean
- branch: feature/cognee-migration, rebased onto main
- secrets: gitignored OK

## Git push
- pushed: feature/cognee-migration -> origin
- commit: abc1234 (head)

## Staging
- timestamp: 2026-04-17 15:32
- backup: restic snapshot 78093fc9
- deploy.sh exit: 0
- health: 200 OK
- staging URL: http://<your-server-ip>:3002
- screenshot: verified OK

## Production
- status: awaiting prince approval
- requested: 2026-04-17 15:40
- approved: ...
- deployed: ...
```

## Cleanup

After ship (success or prod-pending):
- `scripts/return-skill.sh "$RUN_DIR"` — remove rented-skills binaries, keep manifest
- Archive run dir to `runs/archive/` after 30 days (cron)

## Guardrails

- NEVER push --force
- NEVER delete branches without prince OK
- NEVER deploy prod without explicit approval
- NEVER skip DO Spaces backup
- After deploy, always verify health
