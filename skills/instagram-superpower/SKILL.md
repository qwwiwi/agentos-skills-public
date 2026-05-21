---
name: instagram-superpower
description: >
  Full toolkit for Instagram: account analytics via HikerAPI SaaS
  + downloading reels/posts via Cobalt API.
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
| **HikerAPI** | Analytics: profiles, reels, comments, followers, hashtags, search | $0.001/request (Standard) |
| **Cobalt** | Download video/photo from Instagram CDN | Free (self-hosted) |
| **Groq Whisper** | Transcription of downloaded videos | Free |

## Documentation and links

| Resource | URL |
|----------|-----|
| HikerAPI docs | https://hiker-doc.readthedocs.io/en/latest/ |
| HikerAPI Swagger | https://api.instagrapi.com/docs |
| HikerAPI Redoc | https://api.instagrapi.com/redoc |
| HikerAPI dashboard | https://hikerapi.com |
| HikerAPI Python SDK | `pip install hikerapi` |
| Cobalt GitHub | https://github.com/imputnet/cobalt |
| instagrapi GitHub | https://github.com/subzeroid/instagrapi |

## Path mapping

### Agent machine

| What | Path |
|------|------|
| Download script (Cobalt) | `~/.claude/skills/instagram-superpower/scripts/download.sh` |
| Analytics script (HikerAPI) | `~/.claude/skills/instagram-superpower/scripts/analyze.sh` |
| Watchlist script | `~/.claude/skills/instagram-superpower/scripts/watchlist.sh` |
| Cookie deploy script | `~/.claude/skills/instagram-superpower/scripts/deploy-cookies.sh` |
| Cookie check script | `~/.claude/skills/instagram-superpower/scripts/check-cookies.sh` |
| HikerAPI key | `~/.secrets/hikerapi/api-key` |
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
HikerAPI (cloud)                    Cobalt server (self-hosted)
─────────────────                    ────────────────────────────
api.instagrapi.com ◀── curl ──  Your machine
  analytics, data                    Cobalt API (localhost:9000)
  $0.001/request                       media download (free)

Your machine:
  analyze.sh  → HikerAPI (directly)
  download.sh → SSH → Cobalt server → Instagram CDN
  watchlist.sh → analyze.sh + download.sh
```

## HikerAPI — Authentication

```bash
# IMPORTANT: use api.instagrapi.com (no Cloudflare) instead of api.hikerapi.com
# api.hikerapi.com blocks urllib/requests from scripts
cat ~/.secrets/hikerapi/api-key

# Usage in curl:
curl -s "https://api.instagrapi.com/ENDPOINT" \
  -H "accept: application/json" \
  -H "x-access-key: $(cat ~/.secrets/hikerapi/api-key)"

# Or as GET parameter:
curl -s "https://api.instagrapi.com/ENDPOINT?access_key=$(cat ~/.secrets/hikerapi/api-key)"
```

**Balance:** `GET /sys/balance` — shows remaining requests and balance.

## HikerAPI — Main endpoints

### Users

| Endpoint | Description | Requests |
|----------|-------------|---------|
| `GET /v2/user/by/username?username=X` | Profile by username | 1 |
| `GET /v2/user/by/id?id=X` | Profile by ID (faster) | 1 |
| `GET /v2/user/clips?user_id=X` | User reels (12/page) | 1 |
| `GET /gql/user/clips?user_id=X` | Reels via GraphQL | 1 |
| `GET /v1/user/medias/chunk?user_id=X` | All posts (paginated) | 1 |
| `GET /v2/user/stories?user_id=X` | Stories | 1 |
| `GET /v2/user/followers?user_id=X` | Followers (paginated) | 1 |
| `GET /v2/user/following?user_id=X` | Following | 1 |
| `GET /v1/user/highlights?user_id=X` | Highlights | 1 |

### Media (posts/reels)

| Endpoint | Description | Requests |
|----------|-------------|---------|
| `GET /v2/media/info/by/code?code=X` | Info by post code | 1 |
| `GET /v2/media/info/by/url?url=X` | Info by URL | 1 |
| `GET /v2/media/comments?media_id=X` | Comments (15/page) | 1 |
| `GET /v2/media/likers?media_id=X` | Who liked | 1 |
| `GET /v1/media/download/video?media_pk=X` | Download video | 1 |
| `GET /v1/media/download/photo?media_pk=X` | Download photo | 1 |

### Search

| Endpoint | Description | Requests |
|----------|-------------|---------|
| `GET /v2/fbsearch/topsearch?query=X` | Global search | 1 |
| `GET /v2/fbsearch/reels?query=X` | Reel search | 1 |
| `GET /v2/fbsearch/accounts?query=X` | Account search | 1 |
| `GET /v2/fbsearch/places?query=X` | Location search | 1 |

### Hashtags

| Endpoint | Description | Requests |
|----------|-------------|---------|
| `GET /v2/hashtag/by/name?name=X` | Hashtag info | 1 |
| `GET /v2/hashtag/medias/top?hashtag_id=X` | Top posts by hashtag | 1 |
| `GET /v2/hashtag/medias/recent?hashtag_id=X` | Recent posts by hashtag | 1 |

### Response data

Each media object contains:
- `play_count` / `view_count` — views
- `like_count` — likes
- `comment_count` — comments
- `taken_at` — publish timestamp
- `code` — shortcode for URL (`instagram.com/reel/{code}/`)
- `caption.text` — caption text
- `user.username` — author

## Quick start

### Account profile
```bash
HIKER_KEY=$(cat ~/.secrets/hikerapi/api-key)
curl -s "https://api.instagrapi.com/v2/user/by/username?username=<username>" \
  -H "x-access-key: $HIKER_KEY" | python3 -m json.tool
```

### Account reels (top performing)
```bash
HIKER_KEY=$(cat ~/.secrets/hikerapi/api-key)
USER_ID=$(curl -s "https://api.instagrapi.com/v2/user/by/username?username=<username>" \
  -H "x-access-key: $HIKER_KEY" | python3 -c "import json,sys; print(json.load(sys.stdin)['user']['pk'])")

curl -s "https://api.instagrapi.com/v2/user/clips?user_id=$USER_ID" \
  -H "x-access-key: $HIKER_KEY" | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('response',{}).get('items',[])
for item in sorted(items, key=lambda x: x['media'].get('play_count',0), reverse=True)[:5]:
    m = item['media']
    print(f'{m.get(\"play_count\",0):>10,} views | {m.get(\"like_count\",0):>6,} likes | https://instagram.com/reel/{m[\"code\"]}/')
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

### Check HikerAPI balance
```bash
curl -s "https://api.instagrapi.com/sys/balance" \
  -H "x-access-key: $(cat ~/.secrets/hikerapi/api-key)"
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

### 3. "Add to monitoring"
```bash
bash scripts/watchlist.sh add <username>
bash scripts/watchlist.sh scan 3 14
```

### 4. "Full competitor breakdown"
1. `analyze.sh <username> 5 14` → top-5 reels + metrics
2. `download.sh <url> transcribe` for top-3
3. Agent analyzes: hook → pain → solution → CTA

### 5. "What's viral in a hashtag"
```bash
HIKER_KEY=$(cat ~/.secrets/hikerapi/api-key)
curl -s "https://api.instagrapi.com/v2/hashtag/by/name?name=aitools" -H "x-access-key: $HIKER_KEY"
curl -s "https://api.instagrapi.com/v2/hashtag/medias/top?hashtag_id=ID" -H "x-access-key: $HIKER_KEY"
```

## Pagination

Many endpoints return `next_page_id`. For the next page:
```bash
curl -s "https://api.instagrapi.com/v2/user/clips?user_id=123&page_id=NEXT_PAGE_ID" \
  -H "x-access-key: $HIKER_KEY"
```

Reels: ~12 per page. For 50 reels you need ~4 requests.

## Rate Limits

### HikerAPI
- Limit: **8 requests/second** (Standard plan)
- No risk of Instagram ban — HikerAPI uses its own account pool and proxies

### Cobalt (downloads)
- Rate limits Instagram: **20 downloads/hour** per 1 account
- Pause between requests: **minimum 3 seconds**
- Batch downloads (>5): pause **10-15 seconds**
- Strictly sequential, never parallel

### Optimal strategy
- **Analytics** (HikerAPI): no limits, up to 8 req/sec
- **Downloads** (Cobalt): 20/hour, sequential
- HikerAPI can also download (`/v1/media/download/*`), but uses paid requests — use Cobalt instead

## Maintenance

### HikerAPI
```bash
curl -s "https://api.instagrapi.com/sys/balance" -H "x-access-key: $(cat ~/.secrets/hikerapi/api-key)"
# Key in dashboard: https://hikerapi.com → Tokens
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

- HikerAPI key: `~/.secrets/hikerapi/api-key` (chmod 600)
- Cobalt: ONLY `127.0.0.1:9000` on the Cobalt server
- Cookies/credentials: ONLY `~/.secrets/cobalt/` (chmod 600)
- Forbidden: logging keys/cookies, printing in chat, committing to git
