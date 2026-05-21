---
name: learnings
description: >
  Learnings System v2 — self-improvement через scoring ошибок.
  3 слоя: Episodes (сырой лог) → Learnings (scored) → Rules (promoted).
  Используй когда: (1) пользователь поправил действие, (2) обнаружена ошибка,
  (3) нужен отчёт по learnings, (4) lint/audit накопленных уроков.
---

## Архитектура

```
Layer 1: Episodes    — core/learnings/episodes.jsonl (append-only)
Layer 2: Learnings   — core/LEARNINGS.md (scored, max 30)
Layer 3: Rules       — rules.md / CLAUDE.md (promoted, owner only)
```

## CLI

Engine: `~/.claude/scripts/learnings-engine.mjs`

```bash
ENGINE="node ~/.claude/scripts/learnings-engine.mjs"

# Record new episode
echo '{"context":"...","error":"...","rule":"...","impact":"high","tags":["workflow"]}' | $ENGINE capture

# View scored learnings
$ENGINE score

# Lint: find HOT (freq 3+), STALE (score < 0.15), PROMOTE (score > 0.8)
$ENGINE lint

# Promote learning to rules
$ENGINE promote EP-20260411-007

# Archive stale learning
$ENGINE archive EP-20260411-009

# Bump frequency (repeat violation)
$ENGINE bump EP-20260411-001

# Generate markdown report
$ENGINE report
```

## Scoring

Composite score: `Recency (40%) + Frequency (30%) + Impact (30%)`

- Recency: `max(0, 1 - ageDays / 30)` — decay to 0 over 30 days
- Frequency: `min(1, freq / 3)` — 3+ violations = max score
- Impact: critical=1.0, high=0.7, medium=0.4, low=0.1

## Thresholds

| Condition | Action |
|---|---|
| Score > 0.8 | Propose promotion to rules (via owner) |
| Score < 0.15 | Propose archival |
| Freq 3+ in 30 days | ALERT: rule not working, change system |

## When to record

Record ONLY when:
- Owner explicitly corrected ("no, do it this way", "wrong")
- Expensive error (access, security, infrastructure, data)
- Repeated pattern (same mistake twice)
- Owner sets new standard/rule

Do NOT record:
- Normal clarifications
- Choice between options
- Minor style tweaks without pattern

## Episode format

```json
{
  "id": "EP-YYYYMMDD-NNN",
  "ts": "ISO8601",
  "type": "correction|insight|knowledge_gap",
  "agent": "{{AGENT_ID}}",
  "source": "owner|experience|review",
  "context": "situation",
  "error": "what went wrong",
  "rule": "rule for the future",
  "impact": "critical|high|medium|low",
  "tags": ["tag1"],
  "freq": 1,
  "status": "active|promoted|archived"
}
```

## Access zones for auto-fix

| Zone | Files | Who edits |
|---|---|---|
| GREEN | SKILL.md, TOOLS.md, LEARNINGS.md | Agent autonomously |
| YELLOW | AGENTS.md, decisions.md | Agent with justification |
| RED | rules.md, CLAUDE.md | Owner only |

## What to do at freq 3+

| Error type | Action |
|---|---|
| Forgot a step | Add hook (PreToolUse/PostToolUse) |
| Wrong response style | Update CLAUDE.md or rules.md (via owner) |
| Used wrong tool | Update TOOLS.md |
| Asked unnecessary question | Add rule to CLAUDE.md (via owner) |
| Code error | Add test or lint rule |

## Hooks integration

- **SessionStart**: inject scored top-5 from `$ENGINE score`
- **Stop**: analyze session corrections, auto-capture episodes
- **Weekly cron**: `$ENGINE lint` + report to owner
