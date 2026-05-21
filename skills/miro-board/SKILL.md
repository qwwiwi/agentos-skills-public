---
name: miro-board
description: Create lesson presentations and slide layouts on Miro board via MCP API. Use this skill when: (1) user asks to "build a presentation for a lesson", "make workshop/course slides", "slides on Miro", (2) need to create 6+ frames 1920x1080 for video recording, (3) course lessons in Miro, (4) Convert to Slides in Miro, (5) text on the left under face-cam on the right. The skill includes a ready-made system: dark graphite + gold style, font scale, Miro DSL coordinate rules, bulk_create limits, recipe for assembling 6-frame presentations. Triggers: "slides for lesson", "lesson presentation", "miro board", "miro-board", "build slides", "make presentation", "workshop slides", "course slides".
---

# miro-board — lesson presentations on Miro

## When to use

- User asks to "build lesson N presentation" / "slides for lesson" / "workshop presentation"
- Need to prepare a visual layout for recording a video lesson (face-cam right, content left)
- Goal: 6 frames 1920x1080 on Miro board, ready for **Convert to Slides** in Miro UI

## Architecture of one presentation

**Lesson anatomy:** Cover + 5 steps = 6 frames 1920x1080.

```
y=200    Cover           (Lesson · Topic)
y=1380   Step 1          (eyebrow / title / content)
y=2560   Step 2
y=3740   Step 3
y=4920   Step 4
y=6100   Step 5
```

Frames in a vertical column, gap=100 between them. x=200 for all (board origin).

**Layout inside a frame:**
- **Left half** (x=500..1280, w=780): all text
- **Right half** (x=1280..2120, ~840px): empty — for face-cam during recording

x=500 is the absolute coordinate on the board (frame.x=200 + offset 300).

## Style system

| Color | HEX | Where |
|---|---|---|
| Graphite (background) | `#0f0e0b` | fill of all frames |
| Gold (accents) | `#c8a24a` | eyebrows, mono labels, pin quotes, arrows |
| Warm white | `#fcfaf7` | titles, main labels |
| Dim grey | `#8a8275` | subtitles, secondary, descriptions |

**Miro fonts:**
- `eb_garamond` — serif titles (size 58-80 on cover, 28-64 on steps)
- `plex_mono` — eyebrows (UPPERCASE), code-like labels (size 18-24)
- `plex_sans` — bullets, descriptions (size 18-24)
- `plex_serif` — italic pin quotes in frame footer (size 18-22)

Full typographic scale: `references/02-style-system.md`.

## Key rule — coordinates

This is the most common pitfall. Always **read** `references/04-coordinate-rules.md` before the first `layout_create`.

In brief:

- `layout_create` **without** `moveToWidget` → x/y are **ABSOLUTE on the board**, even if DSL has `parent=<frame_url>`. Parent in DSL — logical grouping only, coordinates are not recalculated.
- `layout_create` **with** `moveToWidget=<frame_id>` → x/y are **relative** to frame top-left (frame top-left = 0,0). Must be within `frame.w / frame.h`.
- `image_create` behaves the same: with `moveToWidget` — relative, without — board-absolute.

## Recipe for building a lesson

Full step-by-step process in `references/03-create-lesson.md`. Short version:

### Step 0 — fetch lesson content

Fetch from your data source (database, markdown, etc.) the lesson title, duration, and step descriptions.

### Step 1 — find/create board

```
mcp__miro__board_search_boards query="<course name>"
```

If none — `board_create`.

### Step 2 — create 6 frames with one layout_create

Without moveToWidget, board-absolute coordinates.

```
mcp__miro__layout_create miro_url=<board>
dsl=
f1 FRAME x=200 y=200    w=1920 h=1080 fill=#0f0e0b "Lesson N · Cover"
f2 FRAME x=200 y=1380   w=1920 h=1080 fill=#0f0e0b "Lesson N · Step 1 — ..."
f3 FRAME x=200 y=2560   w=1920 h=1080 fill=#0f0e0b "Lesson N · Step 2 — ..."
f4 FRAME x=200 y=3740   w=1920 h=1080 fill=#0f0e0b "Lesson N · Step 3 — ..."
f5 FRAME x=200 y=4920   w=1920 h=1080 fill=#0f0e0b "Lesson N · Step 4 — ..."
f6 FRAME x=200 y=6100   w=1920 h=1080 fill=#0f0e0b "Lesson N · Step 5 — ..."
```

The response includes frame URLs with `?moveToWidget=<frame_id>`. Save them.

### Step 3 — fill TEXT inside each frame

Here coordinates are **relative** to the frame (important!). Separate `layout_create` per frame with `moveToWidget=<frame_id>`.

Cover template (10 elements):
```
eb  TEXT x=300 y=140  w=780 align=left font=plex_mono   size=22 color=#c8a24a "LESSON N · MM MIN"
t   TEXT x=300 y=300  w=780 align=left font=eb_garamond size=80 color=#fcfaf7 "<Lesson title>"
sub TEXT x=300 y=480  w=780 align=left font=plex_sans   size=24 color=#8a8275 "<Short description (1-2 sentences)>"
h   TEXT x=300 y=640  w=780 align=left font=plex_mono   size=18 color=#c8a24a "WHAT WE COVER"
b1  TEXT x=300 y=720  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— <step 1>"
b2  TEXT x=300 y=765  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— <step 2>"
b3  TEXT x=300 y=810  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— <step 3>"
b4  TEXT x=300 y=855  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— <step 4>"
b5  TEXT x=300 y=900  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— <step 5>"
ft  TEXT x=300 y=1020 w=780 align=left font=plex_mono   size=14 color=#8a8275 "<your-domain>  ·  course name  ·  N / TOTAL"
```

Step template (10-14 elements): eyebrow + title + subtitle + content blocks + pin. Full templates in `references/03-create-lesson.md`.

Note: **x=300** in relative-frame coordinates = x=500 on board (frame.x=200 + 300). This gives the left half for text.

### Step 4 — manual Convert to Slides

This is done by the **user**, not the agent. In Miro UI: right-click on frame → "Convert to Slides". After conversion texts inside frames are preserved as editable slides.

Note: after Convert to Slides, API access to those frames partially breaks. Make all edits **before** Convert to Slides.

## Pitfalls (read before first build)

1. **Bulk limit:** 14+ TEXT items in one `layout_create` fail with `HTTP 400`. Split into groups of 9-12.

2. **Parallel calls on one frame** = race → fail. Finish frame A, then start frame B. Only different frames can be parallelized.

3. **Symbol `✕` (U+2715) breaks the API** → HTTP 400. Alternatives: `—`, `x`, `X`. Safe: `→`, `?`, numbers.

4. **Image widgets in frames for Convert to Slides** — Miro does not pick them up correctly in slide mode. Let the user drag and drop images manually.

5. **HARD RULE: right half of frame = ONLY face-cam.** ALWAYS single column: relative `x=300 w=780` (= board absolute x=500..1280, left half). NEVER make a second column at `x=980` — it overlaps the face-cam zone.

## Content: visual schemes as images vs text

| Scheme | Method |
|---|---|
| Anatomy diagrams (4-block) | TEXT in frame (editable, readable in Convert to Slides) |
| Before/After comparison | TEXT in frame |
| Few-shot pattern | TEXT in frame with `→` arrows |
| Antipatterns grid 2x3 | TEXT in frame |
| Decorative covers | Image generated externally, placed as separate image-widget |

## On-demand references

- `references/01-architecture.md` — board coordinate grid, frame layout, how to add 7th/8th step
- `references/02-style-system.md` — full typographic scale, padding, gap, sizes
- `references/03-create-lesson.md` — step-by-step recipe, full DSL templates cover/step
- `references/04-coordinate-rules.md` — relative vs absolute coordinates in Miro DSL
- `references/05-api-gotchas.md` — bulk limit, frame race, symbol escape, prevention checklist
- `references/06-fetch-content.md` — how to fetch lesson content from your data source (Supabase, etc.)
