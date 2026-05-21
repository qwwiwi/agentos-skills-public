---
name: loop-coding
description: "Orchestrates implementation-heavy coding work — migrations, major refactors, rewrites, multi-file feature builds, auth/API overhauls, system rebuilds — via a 7-phase pipeline (research, audit, plan, implement, review, fix-loop, ship). Scripts-first (70%+ automated), dual-model critique (Opus + Codex), auto-generated helper sub-skills via skill-creator, staging-first deploy. Trigger on: migrate, rewrite, rebuild, overhaul, large feature — including Russian миграция, крупный рефакторинг, переписать, переделать систему, большая фича, лупкодинг. Do NOT use for: single-file edits, fixes under 5 lines, dependency bumps, typo or link fixes, docs-only changes, adding a log line or type hint, code review of existing PRs, ADR or planning-only requests, content writing or naming tasks (use gsd-plan-phase or brainstorming for planning)."
---

# loop-coding

Orchestrator for large coding tasks. I (Silvana/Opus) coordinate; subagents and scripts do the heavy lifting.

## Core principles

1. **Scripts-first.** If a step can be formalized as a shell/python script, it MUST be a script, not an AI call. Scripts are cheaper, faster, deterministic, and free from token drift. AI is reserved for: generating prompts for subagents, reading merged artifacts, making judgment calls, writing actual code, critiquing code.

2. **Codex for critique, Opus for code, double only on Review.** Research is dual (Sonar+Sonnet, parallel). Audit and Plan are Codex GPT-5.5 ONLY — Opus is NOT spawned for these phases (Codex is the stronger critic + architect, and Opus subscription is the scarce resource we protect). Implement is Opus (best in our stack). Review is the only dual-model phase: Codex + Opus in parallel, scripts merge outputs and flag divergence as risk. Rationale: Audit/Plan = single critic is enough when the critic is GPT-5.5; Review = code already exists, two pairs of eyes catch different bugs, worth the Opus token.

3. **Respect existing code.** Before building new, audit what already exists: our repos (your-repos), code in `~/.claude/`, instructions in CLAUDE.md / rules.md / SOUL.md. Do NOT reinvent if a solution already exists.

4. **Auto-generate helper skills when needed.** After audit, if a gap is detected that would repeat 3+ times and has no existing solution, invoke the global `skill-creator` at `~/.claude/skills/skill-creator/` via an Opus subagent with a pre-answered non-interactive brief (otherwise skill-creator's interview phase stalls). Validate every generated sub-skill with `quick_validate.py` before use. `run_eval.py` for trigger evaluation works on Max OAuth; `run_loop.py` description optimization requires `ANTHROPIC_API_KEY` and is blocked in this workspace. Full workflow + path conventions: `references/sub-skill-generation.md`.

5. **Rent external skills safely.** Skills from skills.sh can be downloaded into `rented-skills/{task-id}/` for the duration of the task, but ONLY after passing security scan (`scripts/skill-security-scan.sh`).

6. **Max 3 fix iterations.** If review-fix loop does not converge in 3 iterations, escalate to prince with remaining issues.

7. **Staging-first deploy.** If project has deploy.sh: staging is autonomous, production requires prince explicit "да, на prod". Push to git is autonomous.

## When to use

Trigger on: миграция, переезд, крупный рефакторинг, большая фича, переделать систему, loop-coding, лупкодинг, полная переработка.

Do NOT trigger on: single bug fixes, typo corrections, 1-file edits, planning-only discussions, documentation updates.

**Sibling skill — `fast-loop-coding`** (`~/.claude/skills/fast-loop-coding/SKILL.md`): for tasks 50-300 LOC, 1-3 files, single subsystem, 15-30 min. 4 phases instead of 7, no parallel research, no double review, 1 fix iteration. Use it when task fits its decision tree; escape to this skill mid-task if scope grows past 300 LOC / 3 files / multi-subsystem.

## Workflow

Seven phases, strict order:

```
1. Research    (Sonar + Sonnet + GitHub-scout + skill-scout, parallel)
2. Audit       (Codex GPT-5.5 ONLY; respect existing code)
3. Plan        (Codex GPT-5.5 ONLY — arch + impl + test skeletons brief)
4. Implement   (Opus coder subagents; run tests after each commit)
5. Review      (Codex + Opus parallel; extend tests)  ← only dual-model phase
6. Fix-loop    (max 3 iterations; else escalate)
7. Ship        (git push auto; staging auto; prod requires prince OK)
```

Each phase produces an artifact in the run directory and updates the milestone bar.

## Run directory

Every invocation creates a dedicated directory:

```
~/.claude/loop-coding-runs/{YYYY-MM-DD}-{task-slug}/
├── RESEARCH.md       (phase 1 output)
├── AUDIT.md          (phase 2 output)
├── PLAN.md           (phase 3 output)
├── REVIEW.md         (phase 5/6 output; severity-sorted)
├── FIX-LOG.md        (iteration log)
├── DEPLOY.md         (phase 7 log)
├── tests/            (TDD skeletons from Plan phase)
└── rented-skills/    (external skills used during this task)
```

Artifacts persist after task completion for audit trail. Archived to `runs/archive/` by a monthly cron.

## Phase execution

For each phase, read the corresponding reference file for detailed instructions:

- Phase 1 Research -> `references/phase-1-research.md`
- Phase 2 Audit -> `references/phase-2-audit.md`
- Phase 3 Plan -> `references/phase-3-plan.md`
- Phase 4 Implement -> `references/phase-4-implement.md`
- Phase 5 Review -> `references/phase-5-review.md`
- Phase 6 Fix-loop -> `references/phase-6-fix-loop.md`
- Phase 7 Ship -> `references/phase-7-ship.md`

Cross-cutting concerns:

- GitHub scouting -> `references/github-scout.md` (min 2000 stars, prefer 10k+)
- skills.sh scouting + rent flow -> `references/skill-scout.md`
- Security scan for external skills -> `references/skill-security.md`
- Test strategy per language -> `references/test-strategy.md`
- Auto-generation of sub-skills -> `references/sub-skill-generation.md`

## Scripts (automation backbone)

Every formalizable step has a script. Invoke them, do not reimplement:

| Script | Purpose | Phase |
|---|---|---|
| `scripts/init-run.sh {slug}` | Create run directory, seed templates | pre-1 |
| `scripts/github-search.sh {query}` | `gh search repos stars:>=2000`, returns JSON | 1 |
| `scripts/skill-scout.sh {query}` | Search skills.sh catalog, filter by security | 1 |
| `scripts/skill-security-scan.sh {path}` | Static grep + Codex review, verdict safe/risky/reject | 1 |
| `scripts/rent-skill.sh {url} {run-dir}` | Download into `rented-skills/`, log manifest | 1 |
| `scripts/return-skill.sh {run-dir}` | Clean rented-skills, keep manifest | 7 |
| `scripts/parallel-review.sh {target}` | Spawn Codex + Opus reviewers, merge to REVIEW.md | 2,5 |
| `scripts/merge-reviews.sh {a} {b}` | Two reviews -> consensus + divergence | 2,5 |
| `scripts/loop-controller.sh {run-dir}` | Iteration counter, auto-escalate at 3 | 6 |
| `scripts/milestone-render.sh {phase}` | Render progress bar, send to Telegram | all |
| `scripts/test-runner.sh {lang\|auto}` | pytest (py) / pnpm\|bun\|npm test (ts) / bats (sh) | 4,5 |
| `scripts/commit-atomic.sh {message}` | git add + commit + optional push | 4,7 |
| `scripts/deploy-helper.sh {env}` | Wrapper over project deploy.sh, logs to DEPLOY.md | 7 |
| `scripts/escalate.sh {run-dir}` | Telegram sendDocument to prince after 3 fails | 6 |

Scripts are self-documenting (pass `-h` for usage).

## Model allocation

| Role | Model | Phases |
|---|---|---|
| Orchestrator | Opus 4.6 (me) | all |
| Research-Sonar | Perplexity sonar-pro | 1 |
| Research-Code | Sonnet 4.6 subagent | 1 |
| Research-GitHub | Sonnet 4.6 + gh CLI | 1 |
| Skill-scout | Sonnet 4.6 subagent | 1 |
| Auditor | Codex GPT-5.5 | 2 |
| Architect + planner | Codex GPT-5.5 | 3 |
| Test-skeleton writer | Opus subagent | 3 (only after Codex plan lands) |
| Coder | Opus subagent(s), up to 5 | 4, 6 |
| Reviewer A | Codex GPT-5.5 | 5 |
| Reviewer B | Opus subagent | 5 |

Codex is never used for research (too slow, too expensive) or for code writing (Opus is stronger in our stack). Codex is strictly critic/architect, and is now the SOLE model for Audit and Plan to offload Opus subscription. Opus only enters during Implement, test-skeleton writing under Codex plan, fix-loop, and Review.

## Milestone display

After every phase transition, render and send the bar to prince. Seven segments, one per phase. See `scripts/milestone-render.sh`.

```
▰▱▱▱▱▱▱ 14% · Research
▰▰▱▱▱▱▱ 28% · Audit
▰▰▰▱▱▱▱ 42% · Plan
▰▰▰▰▱▱▱ 57% · Implement
▰▰▰▰▰▱▱ 71% · Review
▰▰▰▰▰▰▱ 85% · Fix-loop
▰▰▰▰▰▰▰ 100% · Ship
```

## Escalation

Hard stops where the loop cannot proceed autonomously:

1. After 3 fix-loop iterations with remaining critical/high issues -> Telegram to prince with REVIEW.md + FIX-LOG.md attached.
2. Before production deploy (always) -> explicit prince approval required.
3. If research finds no viable approach and no patterns exist -> ask prince for direction.
4. If a rented skill fails security scan AND no alternative exists -> report to prince, do not use skill.

Use `scripts/escalate.sh` - it sends the right files with the right caption.

## Starting a run

```bash
RUN_DIR=$(bash scripts/init-run.sh "cognee-migration")
bash scripts/phase-1-research.sh "$RUN_DIR" "migrate to Cognee graph RAG"
bash scripts/parallel-review.sh audit "$RUN_DIR"
```

Orchestration is primarily shell-driven; I step in for judgment calls between phases and to spawn subagents for code-writing tasks.

## Versioning

Current: v1.0 (2026-04-17).

Skill evolves via iteration after real use. Feedback from each run goes into `~/.claude/skills/LEARNINGS.md` and promotes into this SKILL.md when score >= 0.8.
