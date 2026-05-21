# Storage Commands -- Content Engine Reference

Full reference of storage commands for the content pipeline.

## Storage Paths

| Path | Contents | Operations |
|------|-----------|----------|
| `content/telegram/ideas` | Post and video ideas | get, push, patch |
| `content/telegram/sources` | Saved sources (links, articles) | get, push |
| `content/telegram/drafts` | Post drafts | get, push, patch |
| `content/telegram/library` | Reference posts (style library) | get, push |
| `content/telegram/stance/core` | Author position (crypto/macro) | get, put |
| `content/telegram/tone/voice` | Tone of Voice | get, patch |
| `content/telegram/channels/{id}` | Channel profile (persona, rules) | get, patch |
| `content/youtube/channel` | YouTube channel principles | get |
| `learnings` | Lessons from mistakes (for TOV update) | get |

## Commands by Operation

### Ideas

```bash
# Get all ideas
storage-cli get content/telegram/ideas

# Create idea (push returns ID)
storage-cli push content/telegram/ideas '{"title":"Why alts underperform","channel":"@your_channel","status":"idea","created_at":"2025-03-15T12:00:00Z"}'
# → returns: {"name":"<ID>"}

# Update idea status (use ID from push)
storage-cli patch content/telegram/ideas/<ID> '{"status":"in_progress"}'
storage-cli patch content/telegram/ideas/<ID> '{"status":"published"}'
storage-cli patch content/telegram/ideas/<ID> '{"status":"rejected","reason":"no longer relevant"}'
```

Statuses: `idea` → `in_progress` → `published` | `rejected`

### Sources

```bash
# Save source
storage-cli push content/telegram/sources '{"url":"https://example.com/article","type":"article","category":"macro","date":"2025-03-15","summary":"Brief description"}'

# Types: article, tweet, video, report, screenshot, audio
```

### Drafts

```bash
# Save draft
storage-cli push content/telegram/drafts '{"channel":"@your_channel","text":"Draft text...","idea_id":"<ID>","created_at":"2025-03-15T12:00:00Z"}'
# → returns: {"name":"<DRAFT_ID>"}

# Update draft after edits
storage-cli patch content/telegram/drafts/<DRAFT_ID> '{"text":"Updated text...","version":2}'
```

### Library (style library)

```bash
# Get reference posts (3-5 most recent for context)
storage-cli get content/telegram/library

# Add post to library (ONLY after user approval)
storage-cli push content/telegram/library '{"channel":"@your_channel","text":"Published post text...","published_at":"2025-03-15","is_reference":true}'
```

### Stance (position)

```bash
# Get current position
storage-cli get content/telegram/stance/core

# Update position (put replaces fully)
storage-cli put content/telegram/stance/core '"New position on the market..."'
```

### Tone of Voice

```bash
# Get TOV
storage-cli get content/telegram/tone/voice

# Add rule/ban (patch appends, does not replace)
storage-cli patch content/telegram/tone/voice '{"rules":{"bans":["do not use word X"]}}'
```

### Channel Profile

```bash
# Get channel profile
storage-cli get content/telegram/channels/your_channel

# Update profile
storage-cli patch content/telegram/channels/your_channel '{"persona":"updated parameters..."}'
```

## Working with IDs from push

`storage-cli push` returns JSON with key `name` -- this is the record ID:

```bash
# 1. Create record
RESULT=$(storage-cli push content/telegram/ideas '{"title":"Topic","status":"idea"}')
# RESULT = {"name":"-NxAbC123"}

# 2. Extract ID
ID=$(echo $RESULT | jq -r '.name')
# ID = -NxAbC123

# 3. Use for patch
storage-cli patch content/telegram/ideas/$ID '{"status":"in_progress"}'
```

## Local mirrors (fallback)

If storage unavailable, use local files (mark [unverified]):

| Storage path | Local mirror |
|---------------|-------------------|
| `content/telegram/tone/voice` | `~/.claude/skills/content-engine/memory/TONE_OF_VOICE.md` |
| `content/telegram/stance/core` | storage only |
| Workflow | `~/.claude/skills/content-engine/memory/CONTENT_MODE.md` |

## Full pipeline in commands

```bash
# 1. Load context
storage-cli get content/telegram/tone/voice
storage-cli get content/telegram/channels/your_channel
storage-cli get content/telegram/library
storage-cli get content/telegram/stance/core

# 2. Get idea
storage-cli get content/telegram/ideas
# Select → patch status → in_progress

# 3. Save draft
storage-cli push content/telegram/drafts '{"channel":"...","text":"...","created_at":"..."}'

# 4. After approval and publishing
storage-cli push content/telegram/library '{"channel":"...","text":"...","published_at":"..."}'
storage-cli patch content/telegram/ideas/<ID> '{"status":"published"}'
```
