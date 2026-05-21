# Skill Scout (skills.sh)

Find and rent external skills. Always pass security scan first.

## Catalog source

Primary: https://skills.sh/ (public catalog)

Approach:
1. Fetch catalog index (or use search API if available)
2. Filter by keywords from task
3. Score by downloads, rating, maintainer reputation
4. Security scan (see skill-security.md) — MANDATORY
5. If safe -> rent into `rented-skills/{{task-slug}}/`

## Search pattern

```bash
# Approach A: direct fetch + parse
curl -s https://skills.sh/api/search?q={{QUERY}} | jq ...

# Approach B: Sonar-assisted discovery
# "find skills on skills.sh for {{TASK}}"
```

## Rent flow

```bash
bash scripts/rent-skill.sh {{SKILL_URL}} "$RUN_DIR"
```

The script:
1. Downloads to `$RUN_DIR/rented-skills/{{skill-name}}/`
2. Runs `scripts/skill-security-scan.sh` on the downloaded dir
3. If scan = safe -> registers skill locally (temporary path override)
4. If scan = risky -> prompts orchestrator for go/no-go; record in manifest
5. If scan = reject -> delete dir, log rejection

## Manifest format

`$RUN_DIR/rented-skills/.rental-manifest.json`:

```json
{
  "rentals": [
    {
      "name": "prompt-optimizer",
      "source": "https://skills.sh/s/prompt-optimizer",
      "version": "1.2.3",
      "downloaded_at": "2026-04-17T15:20:00Z",
      "security_verdict": "safe",
      "sha256": "abc123...",
      "used_phases": ["research", "plan"]
    }
  ]
}
```

## Return flow

After task completion (Phase 7):

```bash
bash scripts/return-skill.sh "$RUN_DIR"
```

- Removes `rented-skills/*/` directories
- Keeps `.rental-manifest.json` for audit trail
- If a rental is very useful (used 3+ times successfully), flag for permanent install — prince decides

## Internal skill scouting

Before going external, check our own skills:
- `~/.claude/skills/`
- `~/.claude/skills/`
- `~/.claude/shared/skills/`

Read `using-superpowers/SKILL.md` for the catalog. If any fits -> no rent needed.
