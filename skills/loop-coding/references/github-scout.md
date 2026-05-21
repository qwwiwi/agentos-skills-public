# GitHub Scout

Find public solutions with stars >= 2000 (prefer 10k+).

## Primary: gh CLI

```bash
gh search repos "{{QUERY}} stars:>=2000" \
  --sort=stars --order=desc --limit=30 \
  --json=fullName,description,stargazersCount,updatedAt,language,licenseInfo
```

## Secondary: GitHub REST

When need language/topic filters:

```bash
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/search/repositories?q={{QUERY}}+stars:>=2000+language:python&sort=stars&order=desc"
```

## Tertiary: Sonar-assisted

When keywords unclear:

```
"what are the top N github repositories for {{TOPIC}} in 2025-2026,
minimum 2000 stars, with active maintenance?"
```

## Filter pipeline

For each candidate:
1. stars >= 2000 -> proceed, else drop
2. pushed_at within last 12 months -> proceed
3. not archived -> proceed
4. has license -> proceed (OSI-approved preferred)
5. README readable (fetch first 2k chars) -> proceed

Score: stars_weight (0.4) + freshness_weight (0.3) + activity_weight (0.3).

## Shortlist output

Top 5 in `research-github.md`:

```markdown
## {{N}}. {{full_name}} ({{stars}}* / {{last_commit_days}} days)

- License: MIT
- Language: Python
- Relevance: {{why it fits our task, 1-2 sentences}}
- Integration cost: {{low/medium/high}}
- Risks: {{e.g., "no TS support", "heavy deps"}}
```

## Fallback

If shortlist empty:
- Drop language filter, retry
- Drop topic filter, try parent topic
- If still empty -> log "no >=2000* solutions found" and note in RESEARCH.md

## Rate limiting

`gh` CLI authenticated: 5000 req/hr. Unauthenticated REST: 60/hr.
If hitting limit, exponential backoff; do not parallelize more than 3 concurrent calls.
