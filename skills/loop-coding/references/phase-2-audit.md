# Phase 2 — Audit

Codex GPT-5.5 audits the codebase. Single-model phase (Opus removed 2026-04-24 to offload subscription — see core/rules.md "Model role split").

## Inputs
- `RESEARCH.md` from phase 1
- Target codebase path(s) identified in Research

## Auditor

| Model | Focus |
|---|---|
| Codex GPT-5.5 (via `codex exec`) | architecture, dependencies, security, technical debt, code quality, patterns, test coverage, reusable components, migration boundaries |

Single comprehensive prompt — Codex covers what Opus used to cover separately. Opus is NOT spawned for audit.

## Codex prompt (via codex CLI)

```bash
codex exec --skip-git-repo-check "Audit codebase at {{PATH}} for migration to {{TASK}}.
Cover ALL of:
- Architecture and coupling
- Dependency health (outdated, CVE, deprecated)
- Security surface
- Migration risks (data loss, downtime, breaking changes)
- Tests: coverage, quality, gaps
- Code quality hotspots
- Consistency with project patterns (refer to CLAUDE.md, rules.md)
- Reusable components already present
- Suggested boundaries (what to keep, what to rewrite)
Output AUDIT.md with severity-tagged findings [critical]/[high]/[medium]/[low] and sections:
Existing Code, Risks, Missing Tools, Recommendations, Test Coverage Snapshot."
```

## Output

`AUDIT.md` — written directly by Codex, no merge step needed.

Sections:
1. Existing-code inventory — what NOT to rewrite
2. Risks (severity-tagged)
3. Missing-tools gap list — feeds into sub-skill generation
4. Recommendations
5. Test coverage snapshot

## Sub-skill gap detection

After Codex finishes, `scripts/detect-skill-gaps.sh` grep-extracts bullets from the AUDIT.md "Missing Tools" section and prints candidates to stdout (no scoring, no JSON emission). Thin first pass, not an automated gate.

The orchestrator applies the ALL-conditions gate by hand (repetition 3+, no existing solution, under 100 LOC, deterministic) and for each qualifying gap spawns an Opus subagent per `references/sub-skill-generation.md` — which pre-answers skill-creator's interview phase so the subagent does not stall. Generated sub-skills land in `skills/loop-coding/sub-skills/{slug}/` and must pass `quick_validate.py` plus `skill-security-scan.sh` before use in any later phase.

## Guardrails

- No code changes in this phase.
- No new tests written here.
- If audit identifies that the migration is unnecessary (existing solution covers it), surface that to prince before proceeding.
