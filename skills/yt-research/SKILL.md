---
name: yt-research
description: "Research YouTube for content strategy — find what's taking off in a niche, scan competitor channels, rank videos by views and by view-velocity, and pull any video's transcript. Use this WHENEVER you need to research YouTube, find trending/viral videos on a topic, see what's blowing up on YT, scan a competitor's channel, get a YouTube video's transcript or 'what's in this video', or gather YouTube content ideas from what's working — even if the skill isn't named. Search and stats run keyless via yt-dlp; transcripts go through TranscriptAPI; a YouTube Data API key is optional for cleaner search."
homepage: https://github.com/qwwiwi/agentos-skills-public
user-invocable: true
metadata: {"openclaw":{"emoji":"📺","requires":{"bins":["yt-dlp","python3"]},"optionalEnv":["YOUTUBE_API_KEY","TRANSCRIPT_API_KEY"]}}
---

# yt-research — YouTube niche & competitor radar

Find what's taking off on YouTube in your niche, scan competitor channels, rank by virality,
and pull transcripts for analysis. Pairs well with an Instagram radar (e.g. `reel-radar`) and an
X radar — this is the YouTube leg.

Search and stats work **without any API key** via `yt-dlp`. A YouTube Data API key is an optional,
cleaner search path. Transcripts go through TranscriptAPI (see §3).

## When to use

- "What's taking off on YouTube about <niche>?"
- "Scan these competitor channels — what's working for them?"
- "Get the transcript / what's in this video <url>?"
- Gathering proven content ideas before planning a video.

## 1. Niche search + ranking (default, no key)

```bash
python3 scripts/yt_search.py "<query>" --limit 15            # top by views
python3 scripts/yt_search.py "AI agents for business" --by velocity --enrich   # what's accelerating
python3 scripts/yt_search.py "Claude Code" --limit 20 --json # raw JSON for downstream
```

- `--by views` (default) — top by absolute views.
- `--by velocity` — by **view-velocity** (views / days since upload). The best "rising right now"
  signal: a fresh video with high daily velocity matters more than an old one with big-but-slow totals.
  Velocity needs the upload date, so it auto-enables `--enrich` (an extra per-video lookup, slower).
- `--enrich` — adds upload date, likes, comments, channel subscribers per video.

## 2. Scan competitor channels

```bash
python3 scripts/yt_search.py --handles "channelA,channelB" --limit 10 --by velocity --enrich
```

Pulls the latest N videos from each channel (`youtube.com/@handle/videos`) and ranks them — so you
see which formats are firing for a competitor right now. Handle with or without `@`.

### Channel base — `references/watchlist.json`

Keep a persistent base of tracked channels in `references/watchlist.json` (ships as a template —
fill it with your own niche). Each entry: `handle, name, url, channel_id, subs, lang, niche, cadence,
note, added`. Run the radar over the whole base in one line:

```bash
HANDLES=$(python3 -c "import json; d=json.load(open('references/watchlist.json')); print(','.join(c['handle'] for c in d['channels']))")
python3 scripts/yt_search.py --handles "$HANDLES" --by velocity --enrich --limit 8
```

Add a channel: resolve a video/link to its channel (`yt-dlp <url> --print "%(channel)s|%(uploader_id)s|%(channel_id)s|%(channel_follower_count)s"`),
then append an object to `channels[]` (niche from recent titles, cadence from recent upload dates).

## 3. Transcript of a video

```bash
bash scripts/yt_transcript.sh "<youtube_url|id>" [text|json]
```

Transcripts go through **TranscriptAPI.com v2** (a paid API — 100 free credits on signup, no card).

- Endpoint: `GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=<url|id>&format=text&include_timestamp=false&send_metadata=true`
- Auth: `Authorization: Bearer $TRANSCRIPT_API_KEY`. Set the env var, or drop the key in
  `~/.claude/skills/yt-research/secrets/transcript-api-key`.
- Use the **v2** path with the `video_url` param (the old `video_id` path returns 404). Returns clean
  text + metadata (title, author). 1 credit per success.
- Errors: `401` bad key; `402` out of credits; `404` no captions on the video.

Then extract key points, compare competitors' narratives, and build the structure for your own video.

## 4. YouTube Data API v3 (optional, cleaner search)

Official path: `search.list` + `videos.list` + `channels.list`. Enable with `--api`, reads
`YOUTUBE_API_KEY` from env.

```bash
export YOUTUBE_API_KEY=...
python3 scripts/yt_search.py "AI agents" --api --limit 20
```

Setup (once): in Google Cloud, enable **YouTube Data API v3** → create an **API key** → export
`YOUTUBE_API_KEY`. Free quota: **10,000 units/day** (search.list = 100 units/request ≈ 100 searches/day).
Without a key, search and stats still work fully via yt-dlp; only `--api` is unavailable.

## Output

Default — a numbered list: `views | velocity/day | duration — title` + a `channel — url` line.
With `--json` — an array of objects (`id, title, channel, views, likes, comments, upload_date,
velocity, url`) for downstream analysis or writing to your base.

## How to read it (content strategy)

- **High velocity on a fresh video** = a topic on the rise → candidate for your plan now.
- **High absolute views on an old one** = evergreen → a base topic, not urgent.
- Compare the winners' format / title / length — that's what works in the niche.
- Transcript of a top video → extract the structure and points; don't copy, do it better in your voice.

## Limits & notes

- yt-dlp hits public data only — no private analytics of someone else's channel (only the owner has that).
- `--enrich` / `--by velocity` make one request per video — slower for big lists; run in batches.
- Private analytics of YOUR OWN channel needs OAuth (YouTube Analytics API) — separate setup.
- The channel base (`references/watchlist.json`) ships as a template — populate it with your niche.
