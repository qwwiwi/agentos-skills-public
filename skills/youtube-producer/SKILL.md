---
name: youtube-producer
description: >
  YouTube producer for a creator's channel.
  Generates 5 title variants + thumbnail concept based on an idea from a tweet/article/video,
  using proven formulas from top YouTube creators (e.g. Nate Herk: 680K subs, 116K avg views).
  Also provides a hook for the first 30 seconds and a video structure using his patterns.
  ALWAYS use this skill when:
  (1) user shares a tweet, article, or another video and says "make a video on this topic",
  (2) asks for "video title", "come up with a video name", "YouTube title",
  (3) asks for "thumbnail variants", "cover concept", "thumbnail for a video",
  (4) asks for "video hook", "how to start the video", "first seconds of video",
  (5) preparing YouTube content — even if user doesn't name this skill explicitly.
  Triggers: YouTube, video, title for video, thumbnail, cover, hook.
user-invocable: true
metadata: {"openclaw":{"emoji":"","requires":{"bins":["python3"]},"references":["references/title-formulas.md","references/scenario-patterns.md","references/thumbnail-patterns.md","references/nate-corpus.md"]}}
---

# YouTube Producer

YouTube video producer. Learn from top creators, adapt topics from social media, output in target language.

## When to use

User brings:
- Tweet / X post with AI news
- Link to someone else's YouTube video / reel
- New release (Claude/OpenAI/Google/etc.)
- Article or changelog
- Their own experiment ("I built / tested / spent time with X")

Skill outputs:
1. **Video type** — shock claim / demo-first / contrarian / authority-experiment
2. **5 titles** using different formulas with keyword emphasis
3. **Thumbnail concept** — composition + text + color
4. **Hook (30 sec)** — verbatim text of the opening line
5. **Video structure** — 60-90 sec × 7 blocks, 10-14 min total

## Workflow

### Step 1. Classify the source idea

| Source | Default video type |
|----------|------------------------|
| Tweet about a fresh release (Anthropic, OpenAI, Google) | **Shock claim** (type A) |
| Someone else's demo / workflow | **Demo-first** (type B) |
| Controversy / community debate | **Contrarian** (type C) |
| Creator ran their own experiment | **Authority / experiment** (type D) |

If source is unclear — ask: "Is this news or an experiment?"

### Step 2. Generate 5 titles

Use `references/title-formulas.md`. Output exactly 5 variants, **each using a different formula**:

1. **Authority hijack** — big name + verb + tool
2. **Transformation / I Turned** — personal transformation story
3. **Shock number** — percentage/number + superlative
4. **Just Destroyed** — destruction verb + subject
5. **Absolutism / Contrarian** — never/forever/everyone

**Title rules:**
- In the creator's target language
- Under 70 characters (fits mobile thumbnail)
- No filler words: `tutorial`, `how to` (at the start), `guide`, `tips`, abstractions
- Short dash only — no em dashes
- No emoji

**Output format:**
```
1. [Formula] — Title with KEYWORD emphasis
   Why it works: 1 sentence about the trigger

2. ...
```

### Step 3. Thumbnail concept

In one block describe the composition. Use `references/thumbnail-patterns.md`.

Format:
```
Thumbnail:
- Left: [creator face, emotion]
- Right: [specific object / logo / screenshot]
- Text: "[1-2 words, CAPS]" — color: yellow/red/white
- Accent: [arrow / circle / cross]

Image generation prompt:
[ready prompt for Midjourney/GPT Image]
```

### Step 4. Hook (first 30 sec)

Write verbatim text of the opening line — 3-5 short sentences, 25-60 words.

Requirements:
- First phrase ≈ title (verbatim).
- Trigger words: `just`, `destroyed`, `never again`, `in 3 seconds`.
- Last phrase — bridge: "No long intro — let's go."
- No greeting, no "hey everyone".

### Step 5. Video structure

Output 7 blocks × 60-90 sec:
```
0:00–0:30   Hook
0:30–2:00   Context (what's the release/idea)
2:00–2:30   Mid-CTA #1 (subscribe / join channel)
2:30–7:00   Live demo / screen-share
7:00–10:00  Edge cases / gotchas
10:00–12:00 Honest verdict
12:00+      Closing CTA
```

Under each block — 1-2 sentences on what exactly to show.

## Reference library

- `references/title-formulas.md` — 5 title formulas with metrics
- `references/scenario-patterns.md` — hook/flow/retention/CTA patterns
- `references/thumbnail-patterns.md` — composition + generation prompt
- `references/nate-corpus.md` — table of 30 videos with views/likes/comments/ER

## Transcript corpus

`data/transcripts/<video_id>.txt` — transcripts of reference creator videos (plain text + metadata header).

Use when:
- Finding a live quote for a technique
- Checking frequency of trigger words
- Seeing how two blocks were connected

Load only the specific transcript needed — files are 10-50KB.

## Golden rules

1. **Idea first, format second.** Formulas are packaging. First understand what's uniquely valuable (news / transformation / insight).
2. **Don't copy verbatim.** Adapt to your channel and audience language.
3. **One strong verb in the title.** Not three.
4. **Always show WHY a formula will work** for the specific source. Don't output templates without grounding.
5. **If source is weak — say so.** Better to skip a topic than package emptiness as clickbait.

## Antipatterns (never do)

- Titles with `tutorial` / `guide` / `overview` / `how to do`.
- Long titles (>70 chars) — cut off on mobile.
- Questions in parentheses ("Really?", "Or not?") — signal of insecurity.
- Thumbnails without the creator's face — recognition is lost.
- Hook with "hey everyone" — tired, avoid.

## Working cycle "idea → video"

```
[tweet/link/article]
   ↓
[Step 1: classify]
   ↓
[Step 2: 5 titles]  ← USER PICKS ONE
   ↓
[Step 3: thumbnail for chosen title]
   ↓
[Step 4: hook + structure]
   ↓
[creator records]
```

User chooses the title from 5 — only then write thumbnail and hook (they depend on the chosen title).
