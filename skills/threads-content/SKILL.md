---
name: threads-content
description: Converts a Telegram post (typically from a channel) into a Threads thread of 5-8 posts with a banner for the first message and a CTA with UTM at the end. Includes 4 banner templates (negative/positive/transformation/equation in 3D app-icon style + black background) and a proven 7-block thread structure. Use ALWAYS when user says "make a thread", "adapt for Threads", "turn this post into a thread", "take this post and break it into a thread", "find a popular post and make a thread", or shares a forwarded Telegram post and asks for Threads content.
---

# threads-content

Converter: long Telegram posts → Threads thread + banner + CTA link. Goal — repurpose already-proven content (forwards, reach) for Threads growth without generating new ideas.

## Why this skill exists

Long posts that get 50+ forwards on Telegram — the idea resonates. Threads is a separate audience, different format (<=500 chars, threaded), but same idea. Instead of generating new content — take a proven post and adapt it. 10x faster and gives stable results because you're not guessing what will work — you know it already.

## Workflow in 4 steps

### Step 1 — Get the original post

If already shared in the conversation — proceed to step 2.

If user says "find the post about X in my channel" — use your channel access tool (MTProto client, Bot API, etc.) to search messages by keyword or forward count.

When searching for popular posts, sort by `forwards_count` — top-3 from the last 30 days almost always convert well.

### Step 2 — Break post into a thread

Use the 7-block structure from `references/thread-structure.md`:

1. Hook (counter-narrative, breaks the pattern)
2. Case with numbers (personal experience)
3. Main insight (why it works this way)
4. What's actually needed (bulleted list)
5. Alternative (one solution)
6. Proof of value (numbers: before → after)
7. CTA (link to your product/content)

**Compression rule:** if original post is short, merge blocks 2+3 and 4+5. Minimum 5 posts in the thread, maximum 8.

**Platform limit:** 500 characters per post (hard limit for Threads). Check character count before finalizing. Keep 20-30 character buffer for the "N/7" marker.

**Tone of voice is mandatory.** Before writing the first post, load your brand tone of voice guide (keep it in `references/tone-of-voice.md` or similar).

0 emoji. Short dash –. Point first, no preambles.

### Step 3 — Generate banner for first post

The first post in Threads renders with a preview. A banner increases CTR by 30-50% vs a text-only thread.

Open `references/banner-prompts.md` and choose a template:

- **Negative formula** — post-destructor ("X + Y don't work, failure")
- **Positive formula** — "X + Y = win"
- **Transformation** — "before → after"
- **Equation** — clean equation of 3+ components

All templates share visual language (black background #0A0A0A, 3D app-icons, gold accent #C2A878 on winner, red on loser) — recognizable across threads.

```bash
~/.claude/skills/threads-content/scripts/gen-banner.sh \
  --template negative \
  --prompt "Obsidian purple crystal + old notes app → drooping graph = red X" \
  --size 1792x1024 \
  --output /tmp/thread-banner.png
```

**If image generation API is unavailable or billing limit hit:** say so honestly to the user. Fallback options: user generates manually in ChatGPT Plus (copy the prompt), use a different image generation service.

### Step 4 — Send to user for approval

Never publish to Threads without explicit "ok" / "publish" from user — hard rule.

Delivery format: banner as a separate message, then all 7 posts in one message — each inside a code block with "N/7" marker for one-tap copy on mobile.

```bash
~/.claude/skills/threads-content/scripts/send-thread-draft.sh \
  --posts /tmp/thread-posts.txt \
  --banner /tmp/thread-banner.png \
  --slug your-topic-slug
```

Format `/tmp/thread-posts.txt`: posts separated by a line containing only `---`. Empty lines within a post are fine.

## File structure

```
threads-content/
├── SKILL.md                          (this file — workflow)
├── references/
│   ├── thread-structure.md           (7-block template + Threads limits)
│   ├── banner-prompts.md             (4 prompt templates + base style)
│   ├── cta-workshop.md               (CTA variants + UTM convention)
│   └── cognee-vs-obsidian.md         (reference case, 91 forwards)
└── scripts/
    ├── gen-banner.sh                 (gpt-image-1, 4 templates, sizes)
    └── send-thread-draft.sh          (banner + posts in pre-blocks)
```

## When to read which reference

- **Before writing any thread** → `references/thread-structure.md`
- **Before generating banner** → `references/banner-prompts.md`
- **Before writing the 7th post (CTA)** → `references/cta-workshop.md`
- **If user wants "like that successful one"** → `references/cognee-vs-obsidian.md`

## Hard rules (violation = failure)

1. **Publishing to Threads — only after explicit user approval.** Prepare the draft, user says "ok".
2. **Each post <=500 characters.** Hard limit of Threads, not a style guideline.
3. **UTM is mandatory in the CTA post.** Without UTM you can't measure which thread converts — defeats the purpose.
4. **Respect tone of voice exactly.** 0 emoji. Short dash –. Point first, no preambles.
5. **Image generation unavailable — say so honestly.** Don't fake "here's the banner" when there isn't one.
6. **Don't publish anything from the creator's behalf yourself.** All messages go to the user for approval first.
