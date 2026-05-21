---
name: content-engine
version: 5.0.0
description: >
  Content engine. Classify incoming content, write posts, market reports, YouTube scripts,
  X posts, market reviews, voice/audio routing, cross-post, screenshot handling.
  Triggers: "write a post", "make a post", "post about", "record idea", "save as reference",
  "save", "this is my stance", "my position", sending a link, repost, tweet, screenshot,
  audio or voice message.
---

# Content Engine v5

## 1. Routing matrix

| Incoming | Skill / action |
|----------|-----------------|
| YouTube link | `skills/transcript/SKILL.md` → transcript |
| X/Twitter link | `skills/twitter/SKILL.md` → tweet content |
| Voice/audio (.ogg) | `skills/groq-voice/SKILL.md` → transcription |
| Web link | `skills/markdown-new/SKILL.md` (fallback: `skills/chromium/SKILL.md`) |
| Market request | `skills/market-data/SKILL.md` → data + indicators |
| Screenshot/image | Vision models (describe content, extract text) |

Extract content via routing matrix **before** command routing.

## 2. Command routing

**Explicit command → execute:**

| Command | Action |
|---------|----------|
| "write a post" / "make a post" | Post pipeline (§3) |
| "record idea" | Save to ideas storage |
| "this is my stance" / "my position" | Update stance/core |
| "save as reference" | Save to library (is_reference: true) |
| "save" | Save to sources |

**No explicit command → ASK:**

> "Got it, this is [brief summary]. What should I do with it?
> -- write a post / record as idea / save as material / update position / just for reference"

Never guess intent.

## 3. Post pipeline (10 steps)

1. **Channel.** Crypto/macro → main channel. Ambiguous → ask.
2. **Idea.** From user or from ideas storage -- suggest 2-3. After approval → mark status in_progress.
3. **Persona Lock.** Load from channel profile. Override per-task only if explicitly requested.
4. **Context (required sources):**
   - TOV (Tone of Voice): load from your TOV storage
   - Channel profile: load from channel profiles storage
   - Library (3-5 posts): load from library storage
   - Stance (crypto/macro): load from stance/core storage
   - Local mirrors as fallback if storage unavailable
5. **Pre-draft brief.** 1 thesis, 2-4 supporting points, sources. Show to user or go straight to draft (simple tasks).
6. **Draft.** Opus subagent. Pass: persona lock + TOV + library + task. Save to drafts storage.
7. **Fact-check (BEFORE humanizer!).** Verify: numbers not from API, historical dates, quotes, names. Links only from sources, never invented.
8. **Humanizer.** 3 passes per `skills/content-engine/references/humanizer-patterns.md`. DO NOT touch: facts, numbers, levels, position, categoricality.
9. **Show.** Draft + fact-check to user. Silently, without listing steps. Apply edits verbatim, don't soften. Ask: "One-time edit or add to TOV?"
10. **Publish.** ONLY on command. After → offer to save to library. Update idea → status: published.

## 4. Fallbacks

| Situation | Action |
|----------|----------|
| Library empty | Write by TOV + stance, warn: "Library empty, style may be imprecise" |
| Storage unavailable | Local mirrors, mark [unverified] |
| Stance conflict | Ask user: update stance or one-time exception? |
| Cross-post | One draft → adapt for each channel (TOV + profile for each) |

## 5. Market report

On "what's the market doing" / "market overview":
1. Use `skills/market-data/SKILL.md` to collect data (BTC, RSI, F&G, OI, funding, liquidations, SPY, Fed).
2. Apply stance from stance/core storage.
3. Format: price → indicators → macro → conclusion through user's position.

## 6. YouTube

Scripts, descriptions, timecodes -- details in `skills/content-engine/references/youtube-guide.md`.
YouTube scripts go through steps 3-9 of the pipeline (persona lock, context, brief, draft, fact-check, humanizer, show).
Clarify format with user: Shorts / 5-7 min / 15-20 / 30+. Outline → approval → full script.

## 7. Two idea banks

| Bank | Purpose |
|------|----------|
| Content ideas | Posts, videos |
| Project ideas (status=pipeline) | NOT for content |

## 8. TOV update (every 5 posts)

1. Get learnings from storage -- edits for the period.
2. Get library -- recent originals.
3. Patterns (minimum 2 repetitions) → suggest 2-5 rules → after "yes" → update TOV storage.

## 9. Rights and rules

- **ideas, sources, drafts** -- without asking.
- **library** -- only after "add to library".
- **TOV** -- only on explicit request.
- Draft ALWAYS show to user.
- Publish -- ONLY on command.
- Library = main style source.
- Humanizer pass -- MANDATORY between fact-check and show.
- Persona Lock -- MANDATORY before draft.
- Storage commands: full reference in `skills/content-engine/references/storage-commands.md`.
