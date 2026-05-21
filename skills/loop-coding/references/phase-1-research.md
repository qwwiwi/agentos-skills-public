# Phase 1 — Research

Four parallel subagents, then merge into RESEARCH.md.

## Subagents

| ID | Model | Scope | Output |
|---|---|---|---|
| A | Perplexity sonar-pro | web best-practices, benchmarks | `research-web.md` |
| B | Sonnet 4.6 subagent | our repos, OV, Firebase | `research-internal.md` |
| C | Sonnet 4.6 + `gh` CLI | GitHub repos (stars >= 2000) | `research-github.md` |
| D | Sonnet 4.6 subagent | existing skills + skills.sh | `research-skills.md` |

All four run in the same message via parallel Agent calls.

## Subagent A (Sonar) prompt template

```
Research: how do production teams solve {{TASK}} in 2025-2026?
Requirements:
- Cite sources (return_citations: true)
- Focus on: tools, patterns, pitfalls, benchmarks
- Avoid: blog-post marketing, single-author opinions
Produce markdown with sections: Overview, Best Practices, Pitfalls, References.
```

## Subagent B (Code/Internal) prompt template

```
Read these places and summarize what we already have related to {{TASK}}:
- ~/.claude/CLAUDE.md
- ~/.claude/core/rules.md
- ~/.claude/core/MEMORY.md
- Relevant files in /home/openclaw/ on Thrall (via ssh)
- OV semantic search: "{{TASK}} related decisions"
Produce markdown: Existing Assets, Prior Decisions, Reusable Components.
```

## Subagent C (GitHub scout)

Delegates to `scripts/github-search.sh`. See `github-scout.md`.

## Subagent D (Skill scout)

Delegates to `scripts/skill-scout.sh`. See `skill-scout.md` and `skill-security.md`.

## Merging

Script: `scripts/merge-research.sh $RUN_DIR`

Produces `RESEARCH.md` with sections:
1. Task restatement
2. Web best practices (from A)
3. Existing internal assets (from B)
4. GitHub solutions >= 2000 stars (from C; annotated safe/risky/skip)
5. Reusable / rentable skills (from D; with security verdicts)
6. Key risks identified across sources
7. Test strategy hint (which frameworks fit)

## Guardrails

- No test code written in this phase.
- If no source returns useful material, log "no viable patterns" and escalate.
- Respect existing code: if B finds that solution already exists, RESEARCH.md MUST lead with that finding.
