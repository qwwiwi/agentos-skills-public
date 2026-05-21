---
name: fast-loop-coding
description: "Lightweight 4-phase pipeline for small, well-scoped coding tasks (50-300 LOC, 1-3 files, single subsystem, 15-30 min). Plan (Codex) -> Implement (Opus) -> Dual Review (Codex+Opus) -> Ship. NO parallel research, NO audit phase, max 1 fix iteration. Plan single-model (Codex GPT-5.5) to offload Opus subscription; Review still dual because review is where bugs are caught cheap. Trigger on: short feature, small refactor, single hook, single script, isolated bug-fix-with-test, focused config rewrite, adding CLI subcommand. Russian: быстрый рефакторинг, мелкая фича, новый скрипт, хук, скрипт, исправление с тестом, фастлуп, fast-loop-coding, быстрый луп. Do NOT use for: 5-line fixes (just edit), migrations / rewrites / multi-file features (use loop-coding), production deploys, security-sensitive changes, RED files (CLAUDE.md / rules.md / USER.md), tasks crossing 3+ services. ESCAPE: if scope grows past 300 LOC or 3 files mid-task, abort and switch to loop-coding."
---

# fast-loop-coding

Speed-tuned cousin of `loop-coding`. For small, well-scoped tasks where the full 7-phase pipeline is overkill. Target: 3-4x faster than loop-coding.

## Core principle

**Single critic for plan, dual for review.** Loop-coding (full) is dual on Audit/Plan/Review (defence in depth on big surface). Fast-loop drops Audit entirely, keeps Plan single-model (Codex GPT-5.5 — strong enough alone for small scope), and keeps Review dual (Codex+Opus parallel — cheap insurance once the code exists). If surface is small, one Codex plan converges; if not, escape valve to loop-coding. Aligns with `core/rules.md > Model role split`: Codex for critique/architecture, Opus for code, dual only on Review.

## Decision tree (run BEFORE starting)

Use **fast-loop-coding** if ALL true:

- Estimated LOC <= 300
- Files touched <= 3
- Single subsystem (no cross-service coupling)
- Tests fit in one file
- No production deploy (staging OK)
- No RED file edits
- No external API contract changes

If ANY false -> use **loop-coding** (full 7-phase).

If ALL clearly micro (<= 20 LOC, 1 file, no test) -> just edit. No skill needed.

If unsure -> fast-loop-coding. Easy to upgrade mid-task; hard to downgrade.

## 4 phases (vs loop-coding 7)

### Phase 1: Plan (5 min cap) — Codex GPT-5.5

- Single Codex pass: scope, files, est LOC, test cases, rollback
- `codex exec --skip-git-repo-check "<task brief + relevant file paths>"` — Codex reads code itself
- Write `loop-coding-runs/<date>-fast-<slug>/PLAN.md` (template at bottom)
- NO parallel research (Sonar+Sonnet) — task is small, agent context is enough
- NO audit phase (Codex plan covers risk surface inline)
- Opus is NOT used here — saves subscription tokens for Implement and Review

### Phase 2: Implement

- Direct Edit/Write
- Inline tests as you go (or right after)
- Run tests before review (do not punt)

### Phase 3: Review (dual pass — Codex + Opus parallel)

- TWO reviewers in parallel:
  - Codex GPT-5.5: `codex exec --skip-git-repo-check "review uncommitted diff: ..."` (security, architecture, corner cases)
  - Opus `code-reviewer` subagent (readability, consistency, patterns, test quality)
- Merge findings: CRITICAL + HIGH applied inline immediately
- Defer MEDIUM + LOW unless trivial (note in PLAN.md)
- ONE fix iteration max (apply both reviewers' criticals together)
- If review still red after 1 fix -> escape to loop-coding

### Phase 4: Ship

- Commit + push (after review green)
- No staging dance for <= 300 LOC backend changes (unless deploy.sh requires)
- Update `core/hot/handoff.md` if non-obvious decision made
- No `decisions.md` entry unless architectural trade-off

## Escape valve (mid-task upgrade)

ABORT fast and switch to **loop-coding** if:

- Scope balloons past 300 LOC (during implement)
- 4th file needed
- Architectural concern surfaces
- Review found 2+ CRITICALs (signal: under-researched)
- Discovered multi-subsystem coupling
- Test scope explodes (3+ test files)

**How to escape:**
1. Stop implementation
2. `bash skills/loop-coding/scripts/init-run.sh <slug>` (full run dir)
3. Copy current PLAN.md content into Phase 3 input of full pipeline
4. Restart from loop-coding Phase 1 (Research)
5. Mark the fast-run dir as `aborted` in PLAN.md

## What this skill does NOT do (vs loop-coding)

| Step | loop-coding | fast-loop-coding |
|------|-------------|------------------|
| Research | Sonar + Sonnet parallel | none (use context) |
| Audit | Codex GPT-5.5 only | none |
| Plan | Codex GPT-5.5 only (arch + impl) | Codex GPT-5.5 single pass |
| Implement | Opus subagents (parallel) + scaffold-tests | Opus direct |
| Review | Codex + Opus parallel | Codex + Opus parallel |
| Fix-loop | up to 3 iterations (Opus coder) | 1 iteration max (Opus coder) |
| Ship | pre-ship.sh, deploy-helper.sh | direct commit + push |
| Skill auto-gen | skill-creator on gaps | none |
| Rented skills | yes (with security scan) | no |

## When to choose what

**fast-loop-coding** examples:
- Add a `PostToolUseFailure` hook (~80 LOC, 2 files)
- Write a one-shot validation script (~150 LOC)
- Refactor one function (extract helper, simplify)
- Add CLI subcommand to existing tool
- New shell helper + bash test
- Tighten one regex pattern + regression test

**loop-coding** examples:
- Migration (cognee, OpenRouter switch, backend swap)
- Auth/permission rewrite (cross-cutting)
- New skill with sub-skills + scripts
- Anything touching CLAUDE.md / rules.md / USER.md
- Multi-service change (gateway + bot + frontend)
- Phase-gated rollout (dual-write windows, safety gates)

**No skill needed (just edit):**
- Typo fix
- Single comment add
- Constant tweak
- Single-line bugfix
- Renaming one variable

## PLAN.md template (abbreviated)

```markdown
# <slug> — fast-loop

Goal: <one sentence>
Files: <list, absolute paths>
Est LOC: <number>
Tests: <how — file + cases>
Rollback: <command or revert hash>

## Steps
1. <step>
2. <step>
3. <step>

## Risks
- <risk> -> <mitigation>

## Review verdict
(filled after Phase 3)

## Ship
(filled after Phase 4: commits, push, handoff entry)
```

## Init

```bash
bash ~/.claude/skills/fast-loop-coding/scripts/init-fast-run.sh <slug>
# prints run-dir path
```
