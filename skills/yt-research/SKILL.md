---
name: yt-research
description: "Research YouTube for content strategy — find what's taking off in a niche, scan competitor channels, rank videos by views and by view-velocity, read comments, see trending Shorts, and pull any video's transcript. Use this WHENEVER you need to research YouTube, find trending/viral videos on a topic, see what's blowing up on YT, scan a competitor's channel, get a YouTube video's transcript or 'what's in this video', or gather YouTube content ideas from what's working — even if the skill isn't named. Data comes from Loore (LOORE_API_KEY); the official YouTube Data API v3 (YOUTUBE_API_KEY) is an optional alternative for search, channels and comments. Never scrape YouTube from this machine."
homepage: https://github.com/qwwiwi/agentos-skills-public
user-invocable: true
metadata: {"openclaw":{"emoji":"📺","requires":{"bins":["python3"]},"env":["LOORE_API_KEY"],"optionalEnv":["LOORE_SPEND_AUTHORIZATION_ID","YOUTUBE_API_KEY"]}}
---

# yt-research — YouTube niche & competitor radar

Find what's taking off on YouTube in your niche, scan competitor channels, rank by virality,
read comments and pull transcripts for analysis. Pairs well with an Instagram radar (e.g.
`reel-radar`) and an X radar — this is the YouTube leg.

**Where the data comes from.** YouTube data is read only through [Loore](https://loore.ai)
(default, docs: https://docs.loore.ai) or the official **YouTube Data API v3** (optional `--api`).
Do not scrape YouTube from your own IP — no yt-dlp, innertube, oEmbed or transcript sites for
data. yt-dlp is acceptable only to download a video file itself, and this skill does not need that.

## Setup

```bash
export LOORE_API_KEY="..."   # https://app.loore.ai → Настройки → API и MCP (shown once; never in chat or git)
```

**Spend approval.** Every Loore YouTube call is paid (search, channel, video, comments, trending:
1.5 credits per call; transcript: 2 credits, only when one is returned). An empty page or an upstream
error is free. State the total cap in credits to the user once, and after their «yes» create a flow
budget (valid 24 hours):

```bash
python3 scripts/_loore.py approve --flow yt-research --cap 100
export LOORE_SPEND_AUTHORIZATION_ID=<printed id>
```

The scripts send `spend_authorization_id` with every paid call, including every next page. Without
it Loore answers `428 needs_user_confirmation`. On `429` the client waits `Retry-After`; when the
window resets later than 120 seconds (daily budget), it stops with exit code 4 and prints when to rerun.

**MCP instead of scripts.** The same operations are MCP tools on `https://mcp.loore.ai/mcp`
(header `Authorization: Bearer <key>`): `yt_search`, `yt_channel`, `yt_channel_videos`,
`yt_channel_shorts`, `yt_video`, `yt_comments`, `yt_transcript`, `yt_trending_shorts`
(`yt_search` ↔ `POST /v1/yt-search`). Full list: https://docs.loore.ai/mcp/tools.

## When to use

- "What's taking off on YouTube about <niche>?"
- "Scan these competitor channels — what's working for them?"
- "What are people saying under this video?"
- "Get the transcript / what's in this video <url>?"
- Gathering proven content ideas before planning a video.

## 1. Niche search + ranking (Loore `yt_search`)

```bash
python3 scripts/yt_search.py "<query>" --limit 15            # top by views
python3 scripts/yt_search.py "AI agents for business" --by velocity --enrich   # what's accelerating
python3 scripts/yt_search.py "Claude Code" --limit 20 --json # raw JSON for downstream
python3 scripts/yt_search.py "Claude Code" --upload-date this_week --sort popular --region US
python3 scripts/yt_search.py "AI agents" --type shorts --limit 20
```

- `--by views` (default) — top by absolute views.
- `--by velocity` — by **view-velocity** (views / days since upload). The best "rising right now"
  signal: a fresh video with high daily velocity matters more than an old one with big-but-slow totals.
  Search dates are approximate (YouTube shows «3 weeks ago»); rows without a date are enriched
  automatically.
- `--enrich` — exact upload date, likes, comments (`yt_video`) and channel subscribers
  (`yt_channel`, once per channel). One paid call per video — run on short lists.
- Filters map to `yt_search` parameters: `--upload-date` (today / this_week / this_month /
  this_year), `--sort` (relevance / popular), `--length` (under_3_min / between_3_and_20_min /
  over_20_min), `--region` (two-letter code), `--type` (videos / shorts).
- Pages follow `nextCursor` until `--limit` is reached (at most 5 pages per search or channel).

## 2. Scan competitor channels (Loore `yt_channel_videos` / `yt_channel_shorts`)

```bash
python3 scripts/yt_search.py --handles "channelA,channelB" --limit 10 --by velocity --enrich
python3 scripts/yt_search.py --handles "channelA" --shorts --limit 20      # the channel's Shorts
```

Pulls the latest N long-form videos (or, with `--shorts`, the newest Shorts) of each channel and
ranks them — so you see which formats are firing for a competitor right now. Handle with or without
`@`, or a `UC…` channel id.

### Trending Shorts (Loore `yt_trending_shorts`)

```bash
python3 scripts/yt_search.py --trending-shorts --limit 48
```

About 48 Shorts trending on YouTube right now, one call.

### Channel base — `references/watchlist.json`

Keep a persistent base of tracked channels in `references/watchlist.json` (ships as a template —
fill it with your own niche). Each entry: `handle, name, url, channel_id, subs, lang, niche, cadence,
note, added`. Run the radar over the whole base in one line:

```bash
HANDLES=$(python3 -c "import json; d=json.load(open('references/watchlist.json')); print(','.join(c['handle'] for c in d['channels']))")
python3 scripts/yt_search.py --handles "$HANDLES" --by velocity --enrich --limit 8
```

Add a channel: read it with Loore `yt_channel` (by handle, `UC…` id or any channel link) —
name, subscribers, video totals, country, keywords:

```bash
python3 scripts/_loore.py call yt-channel '{"url": "https://www.youtube.com/@name"}'
```

then append an object to `channels[]` (niche from recent titles, cadence from recent upload dates).

## 3. Comments under a video (Loore `yt_comments`)

```bash
python3 scripts/yt_search.py --comments "<youtube_url|id>" --order top --limit 30
python3 scripts/yt_search.py --comments "<youtube_url|id>" --order newest --json
```

Output: `likes | replies — author: text`. With `--json` each comment also carries `replies_token`;
read a thread with `python3 scripts/_loore.py call yt-comments '{"replies_token": "<token>"}'`.

## 4. Transcript of a video (Loore `yt_transcript`)

```bash
bash scripts/yt_transcript.sh "<youtube_url|id>" [text|json]
```

- Public captions of any video or Short, any length (no AI transcription). Long transcripts come
  in windows (`truncated` / `nextOffset`); the script reads them all.
- `text` prints a `# title — channel` header (one `yt_video` call) and the plain transcript;
  `json` prints `{video_id, language, transcript, metadata}`.
- More options (timestamps, caption language, original audio only, no header) —
  `python3 scripts/yt_transcript.py --help`.
- No captions → exit 4 and the list of caption languages the video has.
- The official YouTube Data API cannot download captions of other people's videos (`captions.download`
  works only for videos you can edit), so there is no API alternative for transcripts.

Then extract key points, compare competitors' narratives, and build the structure for your own video.

## 5. YouTube Data API v3 (optional alternative)

Official path for search, channel videos and comments. Enable with `--api`; reads `YOUTUBE_API_KEY`
from the environment and sends it in the `X-goog-api-key` header (never in a URL or command line).

```bash
export YOUTUBE_API_KEY=...
python3 scripts/yt_search.py "AI agents" --api --limit 20                 # search.list + videos.list
python3 scripts/yt_search.py --handles "channelA" --api --limit 20        # channels.list + playlistItems.list + videos.list
python3 scripts/yt_search.py --comments "<url>" --api --order newest      # commentThreads.list
```

Setup (once): in Google Cloud, enable **YouTube Data API v3** → create an **API key** → export
`YOUTUBE_API_KEY`. Free quota: **10,000 units/day** (search.list = 100 units/request ≈ 100 searches/day;
channel, video and comment reads ≈ 1 unit each). Not available on this path: Shorts lists, trending
Shorts and transcripts (use Loore).

## Output

Default — a numbered list: `views | velocity/day | duration — title` + a `channel — url` line.
With `--json` — an array of objects (`id, title, channel, views, likes, comments, duration,
upload_date, velocity, url`, plus `channel_subs` after `--enrich`) for downstream analysis or
writing to your base.

## How to read it (content strategy)

- **High velocity on a fresh video** = a topic on the rise → candidate for your plan now.
- **High absolute views on an old one** = evergreen → a base topic, not urgent.
- Compare the winners' format / title / length — that's what works in the niche.
- Transcript of a top video → extract the structure and points; don't copy, do it better in your voice.

## Limits & notes

- Public data only — no private analytics of someone else's channel (only the owner has that).
- `--enrich` / `--by velocity` make one paid call per video — run on short lists, in batches.
- Private analytics of YOUR OWN channel needs OAuth (YouTube Analytics API) — separate setup.
- Loore errors: `401` key, `402` out of credits, `403` key not allowed this method, `428` spend
  approval needed — the script stops with a hint; `429` waits or stops with a rerun time.
- The channel base (`references/watchlist.json`) ships as a template — populate it with your niche.
