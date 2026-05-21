---
name: reels
description: "Create a production brief (ТЗ) for Instagram Reels: teleprompter script and editor brief. Triggers: /reels, 'write a reel', 'reel brief', 'create reel script', 'editor brief', link to an Instagram reel + adaptation request. Downloads a reference reel, transcribes it, analyzes structure, generates an HTML doc with two blocks: teleprompter script (with timings) and editor brief (visuals, transitions, on-screen text). Format: HTML with dark theme. NOT for: posting reels, video editing, account analytics."
---

# Reels — Production Brief for Instagram Reels

## Process

### Option A: Adapting a reference reel
1. Get the reference reel link
2. Download via `scripts/download.sh` (from instagram-superpower skill)
3. Transcribe via `mlx_whisper` or groq-voice
4. Get metrics via HikerAPI (`media/by/code`)
5. Analyze script structure
6. Adapt to your language and brand voice
7. Generate HTML

### Option B: Script from scratch
1. Get the topic from the user
2. Load your tone of voice guide
3. Write script using the formulas below
4. Generate HTML

## Script formulas

### "STOP doing X" (proven: 100K+ views)
```
HOOK (0-3 sec): Forbid a familiar action
PROBLEM (3-12 sec): Why it's wrong
SOLUTION (12-25 sec): The right way + examples
PROOF (25-30 sec): Specific result
INSTRUCTIONS (30-42 sec): Step-by-step how-to
BACKUP (42-46 sec): Alternative
CTA (46-50 sec): "Write [WORD] in comments"
```

### "You didn't know X can do Y" (proven: 25K+ views)
```
HOOK (0-3 sec): X can do more than you think
LIST (3-40 sec): 3-5 features with demos
CTA (40-45 sec): "Write [WORD] in comments"
```

### "Step-by-step guide" (proven: 25K+ views)
```
HOOK (0-3 sec): Let's break down N steps on [topic]
STEPS (3-45 sec): Step by step with screen demos
CTA (45-50 sec): "Write [WORD] in comments"
```

## HTML document structure

HTML generated using the `present` skill (dark theme design system).

### Required blocks (in this order):

#### 1. Header
- Badge: "Reel Script"
- Topic name
- Metadata: duration, keyword, format

#### 2. Reference original (if adapting)
- Author (@username)
- Reel link
- Metrics: views, comments, shares, likes, ER
- Block "Why it worked" — 3-5 reasons

#### 3. Teleprompter script
- Clean text for reading
- Large font (1.15rem+), high line-height (2)
- Pauses between blocks (`— pause —`)
- No technical notes — speech only

#### 4. Editor brief — second-by-second breakdown
- Timeline with timecodes (0-3 sec, 3-12 sec, ...)
- For each block:
  - **Speech** (what the presenter says) — in quote-block
  - **On screen** (what to show) — in tip-card
    - Text overlays
    - Screenshots/screencasts to insert
    - Transitions between blocks
    - Code to show in terminal

#### 5. Script formula
- Brief diagram of the structure

#### 6. CTA card
- Keyword prominently displayed
- Keyword stats (if available)

### NOT to include:
- Reel caption — user writes it themselves
- Hashtags

## Keywords for CTA

Common keyword patterns:
- Use a keyword that relates to the reel topic
- Track keyword conversion in your automation system (e.g. ChatPlace, ManyChat)
- Choose the keyword per reel topic for tracking

## Reel parameters

| Parameter | Value |
|----------|------|
| Duration | 30-60 sec (sweet spot for algorithm) |
| Format | Talking head + screencast/text overlay |
| Speaker | Creator (on camera) |
| Editor | Receives HTML doc as brief |

## Tools

| Task | Tool |
|------|------|
| Download reference reel | `instagram-superpower/scripts/download.sh` |
| Transcribe | `mlx_whisper` or `groq-voice/transcribe.sh` |
| Reel metrics | HikerAPI `media/by/code` |
| Author metrics | HikerAPI `user/by/username` |
| HTML generation | `present` skill (dark theme) |

## Example request

User sends:
> https://www.instagram.com/reel/ABC123/ — create a production brief

Agent:
1. Downloads the reel
2. Transcribes it
3. Gets metrics (views, comments, shares, likes)
4. Analyzes structure
5. Adapts to your language/brand voice
6. Selects a CTA keyword
7. Generates HTML with two blocks: teleprompter + editor brief
8. Sends as a document
