---
name: instagram-superpower
description: >
  Full toolkit for Instagram: account analytics via Loore (MCP + REST, https://docs.loore.ai)
  + downloading reels/posts via Cobalt API (or Loore ig_download).
  Use when: (1) download a reel/video/photo from Instagram, (2) find top-performing reels of an account,
  (3) analyze a competitor (views, likes, comments, engagement), (4) manage a watchlist
  of accounts for monitoring, (5) download + transcribe video, (6) hashtag/location search.
  Triggers: "download reel", "download from instagram", "analyze account", "viral reels",
  "top reels", "watchlist", "track account", "competitor instagram", "engagement",
  links to instagram.com/reel/, instagram.com/p/, instagram.com/stories/.
  NOT for: YouTube, Twitter, mass spam, auto-likes, auto-follows.
---

# Instagram SuperPower

## Tools

| Tool | Purpose | Cost |
|------|---------|------|
| **Loore** | Analytics: profiles, reels, posts, comments, followers/following, hashtags, places, search, reel transcripts, file downloads | Credits per request, see https://loore.ai |
| **Cobalt** | Download video/photo from Instagram CDN | Free (self-hosted) |
| **Groq Whisper** | Transcription of downloaded videos | Free |

## Documentation and links

| Resource | URL |
|----------|-----|
| Loore docs | https://docs.loore.ai |
| Loore tool list | https://docs.loore.ai/mcp/tools |
| Loore OpenAPI contract | https://app.loore.ai/api/openapi.json |
| Loore dashboard (API key) | https://app.loore.ai → Настройки → API и MCP |
| Cobalt GitHub | https://github.com/imputnet/cobalt |

## Path mapping

### Agent machine

| What | Path |
|------|------|
| Download script (Cobalt) | `~/.claude/skills/instagram-superpower/scripts/download.sh` |
| Analytics script (Loore REST) | `~/.claude/skills/instagram-superpower/scripts/analyze.sh` |
| Watchlist script | `~/.claude/skills/instagram-superpower/scripts/watchlist.sh` |
| Cookie deploy script | `~/.claude/skills/instagram-superpower/scripts/deploy-cookies.sh` |
| Cookie check script | `~/.claude/skills/instagram-superpower/scripts/check-cookies.sh` |
| Loore key | env `LOORE_API_KEY` (or your agent's secret store) |
| Instagram credentials (for Cobalt) | `~/.secrets/cobalt/accounts.json` |
| Instagram cookies (for Cobalt) | `~/.secrets/cobalt/cookies.json` |
| Cobalt API key | `~/.secrets/cobalt/api-key` |
| Watchlist | `~/.secrets/cobalt/watchlist.json` |
| Downloaded files | `/tmp/downloads/` |

### Cobalt server (self-hosted)

| What | Path |
|------|------|
| Cobalt Docker Compose | `/opt/cobalt/docker-compose.yml` |
| Cobalt cookies (working copy) | `/opt/cobalt/cookies.json` |
| Cobalt API keys | `/opt/cobalt/keys/api-keys.json` |
| Docker container | `cobalt-api` |
| Cobalt API endpoint | `http://127.0.0.1:9000/` (localhost only) |

### How it all connects

```
Loore (cloud)                        Cobalt server (self-hosted)
─────────────────                    ────────────────────────────
mcp.loore.ai  ◀── MCP / REST ──  Your machine
  analytics, data                    Cobalt API (localhost:9000)
  credits per request                  media download (free)

Your machine:
  agent       → Loore MCP tools (ig_profile, ig_user_reels, ...)
  analyze.sh  → Loore REST (directly)
  download.sh → SSH → Cobalt server → Instagram CDN
  watchlist.sh → analyze.sh + download.sh
```

## Loore — Authentication

One key, two doors. Create the key at https://app.loore.ai → Настройки → API и MCP
(the plaintext is shown once). Keep it in `LOORE_API_KEY`, never in chat or git.

**MCP** (preferred for the agent) — add the server to your client config:

```json
{
  "mcpServers": {
    "loore": {
      "type": "http",
      "url": "https://mcp.loore.ai/mcp",
      "headers": { "Authorization": "Bearer <YOUR_KEY>" }
    }
  }
}
```

**REST** (scripts) — the same operation, MCP tool `ig_profile` = `POST /v1/ig-profile`:

```bash
curl -s -X POST https://mcp.loore.ai/v1/ig-profile \
  -H "Authorization: Bearer $LOORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username":"<username>"}'
```

Answer envelope: `{"status":"ok","result":{...}}` or `{"status":"error","error":"...","details":{...}}`.

**Spend approval.** Paid calls need the user's approval. State the total cap in
credits once, and after the user's «yes» create a flow budget with
`spend_authorization` (`action: "create"`, `flow_id`, `approved_cap_credits`,
`user_approved: true`, valid 24 hours); pass the returned `spend_authorization_id`
in every covered paid call (`analyze.sh` reads it from `LOORE_SPEND_AUTHORIZATION_ID`).
Without it Loore answers `428 needs_user_confirmation`.

**Balance:** `get_credit_balance` (`POST /v1/billing-balance`) — free, shows `creditsRemaining`.

## Loore — Main tools

MCP tool name ↔ REST path: `ig_user_reels` ↔ `POST /v1/ig-user-reels`. Full list:
https://docs.loore.ai/mcp/tools.

### Users

| Tool | Description |
|------|-------------|
| `ig_profile` | Profile by `username` or `user_id`: id, followers, following, posts, bio, category |
| `ig_user_reels` | Account reels with views/likes/comments/saves/shares, up to 50 per page |
| `ig_user_posts` | Feed posts (photos, carousels, videos), up to 50 per page |
| `ig_user_stories` | Currently active stories (story id for `ig_download`) |
| `ig_followers` | Followers (paginated, or `collect` into a file) |
| `ig_following` | Following (paginated, or `collect` into a file) |
| `ig_highlights_list` / `ig_highlight_items` | Highlights and their items |
| `ig_analytics` | Ready metrics for a handle: engagement, content mix, posting windows, hashtags, top reels (`depth`: quick / full) |

### Media (posts/reels)

| Tool | Description |
|------|-------------|
| `ig_media` | One post/reel by link or shortcode, whole caption |
| `ig_resolve` | What a link is (reel, post, story, profile) and its canonical id |
| `ig_media_comments` / `ig_comment_replies` | Comments and threads |
| `analyze_reel` | Reel transcript with timecodes, metrics, outlier score vs the author's median, frames on `depth: deep` |
| `video_transcribe` | Word-timed transcript of a reel |
| `ig_download` | The file of a post/reel/story: `downloadUrl` (no key, ~15 minutes) |

### Search

| Tool | Description |
|------|-------------|
| `ig_search` | `kind`: accounts / reels / hashtags / places, plus `query` |
| `ig_hashtag_media` | Publications under a hashtag, `rank`: top / recent / reels |
| `ig_location_media` | Publications at a place (`location_id` from `ig_search kind=places`) |

### Response data

Each media row (`ig_user_reels`, `ig_user_posts`, `ig_search`, `ig_hashtag_media`) contains:
- `views` — plays (reels and videos only)
- `likes` — likes (absent and `likesHidden: true` when the author hid them)
- `comments` — comments
- `saves`, `shares`, `reposts` — reels (absent means not received, not zero)
- `takenAt` — publish time, ISO-8601 UTC
- `code` — shortcode, `url` — permalink
- `caption` — caption text when `include_caption: true` (500 chars; `ig_media` gives the whole caption)
- `author` — author handle
- `isPinned`, `isTrial` — leave such rows out of the author's median

## Quick start

### Account profile
MCP: `ig_profile` with `{"username": "<username>"}`. REST:
```bash
curl -s -X POST https://mcp.loore.ai/v1/ig-profile \
  -H "Authorization: Bearer $LOORE_API_KEY" -H "Content-Type: application/json" \
  -d '{"username":"<username>"}' | python3 -m json.tool
```

### Account reels (top performing)
MCP: `ig_user_reels` with `{"username": "<username>", "limit": 50}`, sort by `views`. REST:
```bash
curl -s -X POST https://mcp.loore.ai/v1/ig-user-reels \
  -H "Authorization: Bearer $LOORE_API_KEY" -H "Content-Type: application/json" \
  -d "{\"username\":\"<username>\",\"limit\":50,\"spend_authorization_id\":\"$LOORE_SPEND_AUTHORIZATION_ID\"}" \
  | python3 -c "
import json, sys
items = json.load(sys.stdin).get('result', {}).get('items', [])
for m in sorted(items, key=lambda x: x.get('views', 0), reverse=True)[:5]:
    print(f'{m.get(\"views\",0):>10,} views | {m.get(\"likes\",0):>6,} likes | {m[\"url\"]}')
"
```

### Download reel (via Cobalt)
```bash
bash ~/.claude/skills/instagram-superpower/scripts/download.sh "https://www.instagram.com/reel/<CODE>/"
```

### Download + transcribe
```bash
bash ~/.claude/skills/instagram-superpower/scripts/download.sh "https://www.instagram.com/reel/<CODE>/" transcribe
```

### Check Loore balance
MCP: `get_credit_balance` (free). REST:
```bash
curl -s -X POST https://mcp.loore.ai/v1/billing-balance \
  -H "Authorization: Bearer $LOORE_API_KEY" -H "Content-Type: application/json" -d '{}'
```

## Typical scenarios

### 1. "Show top reels of a competitor"
```bash
bash scripts/analyze.sh <username> 5 14
```

### 2. "Download this reel and summarize it"
```bash
bash scripts/download.sh "<url>" transcribe
```
Cobalt downloads → Groq transcribes → agent analyzes.
Alternative without Cobalt and Groq: Loore `analyze_reel` (`depth: "quick"` — caption,
metrics, transcript with timecodes) or `video_transcribe` (word-timed transcript).

### 3. "Add to monitoring"
```bash
bash scripts/watchlist.sh add <username>
bash scripts/watchlist.sh scan 3 14
```

### 4. "Full competitor breakdown"
1. `analyze.sh <username> 5 14` → top-5 reels + metrics
2. `download.sh <url> transcribe` for top-3 (or Loore `analyze_reel` per reel)
3. Agent analyzes: hook → pain → solution → CTA

### 5. "What's viral in a hashtag"
MCP: `ig_hashtag_media` with `{"hashtag": "aitools", "rank": "top"}` (or `"reels"` for video only).
REST:
```bash
curl -s -X POST https://mcp.loore.ai/v1/ig-hashtag-media \
  -H "Authorization: Bearer $LOORE_API_KEY" -H "Content-Type: application/json" \
  -d '{"hashtag":"aitools","rank":"top","limit":50}'
```
Places: `ig_search` `{"kind": "places", "query": "..."}` → `ig_location_media` with the place id.

## Pagination

List tools answer `hasMore` and, when it is true, `nextCursor`. Pass it back unchanged
as `cursor` for the next page (`limit` up to 50; above 50 is refused, not clamped):
```bash
curl -s -X POST https://mcp.loore.ai/v1/ig-user-reels \
  -H "Authorization: Bearer $LOORE_API_KEY" -H "Content-Type: application/json" \
  -d '{"username":"<username>","limit":50,"cursor":"<nextCursor>"}'
```

A cursor is valid for 6 hours; after that the walk restarts from page one.

## Rate Limits

### Loore
- Budgets per key, per minute and per day, depending on the plan; current values in the dashboard
- On `429` — wait (`details.retry_after_seconds`) and retry; on `401` / `402` / `403` / `428` — stop and tell the user
- Heavy calls (`analyze_reel`, `ig_download`) cost more — do not loop them "just in case"

### Cobalt (downloads)
- Rate limits Instagram: **20 downloads/hour** per 1 account
- Pause between requests: **minimum 3 seconds**
- Batch downloads (>5): pause **10-15 seconds**
- Strictly sequential, never parallel

### Optimal strategy
- **Analytics** (Loore): one meaningful call instead of ten; `ig_analytics` gives a whole account in one request
- **Downloads** (Cobalt): 20/hour, sequential
- Loore can also download (`ig_download`, paid per file) — use it when Cobalt is not set up

## Maintenance

### Loore
```bash
curl -s -X POST https://mcp.loore.ai/v1/billing-balance \
  -H "Authorization: Bearer $LOORE_API_KEY" -H "Content-Type: application/json" -d '{}'
# Key in dashboard: https://app.loore.ai → Настройки → API и MCP (revoke a leaked key there)
```

### Cobalt
```bash
ssh root@<your-server-ip> "docker ps --filter name=cobalt-api --format '{{.Status}}'"
ssh root@<your-server-ip> "docker logs cobalt-api --tail 20"
ssh root@<your-server-ip> "cd /opt/cobalt && docker compose restart cobalt-api"
```

## Updating Instagram cookies (for Cobalt)

1. Credentials: `~/.secrets/cobalt/accounts.json`
2. Login via browser automation (agent-browser via CDP)
3. Login using `Input.dispatchKeyEvent` (character by character)
4. Button: `div[role="button"]`
5. 2FA: TOTP → `input[name="verificationCode"]`
6. Cookies: `Network.getCookies` → `.instagram.com` → `cookies.json`
7. Deploy: `bash scripts/deploy-cookies.sh`

## Security

- Loore key: env `LOORE_API_KEY` only, header `Authorization: Bearer` (never in URL, chat or git)
- Cobalt: ONLY `127.0.0.1:9000` on the Cobalt server
- Cookies/credentials: ONLY `~/.secrets/cobalt/` (chmod 600)
- Forbidden: logging keys/cookies, printing in chat, committing to git
