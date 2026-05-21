# 03 — Create lesson presentation (full recipe)

## Step 0 — fetch lesson content

```bash
export SUPABASE_PROJECT_REF="<your-project-ref>"
export SUPABASE_ACCESS_TOKEN="<your-access-token>"
export SUPABASE_MGMT_API="https://api.supabase.com"

curl -sS "$SUPABASE_MGMT_API/v1/projects/$SUPABASE_PROJECT_REF/database/query" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT lesson_number, title, duration_minutes, summary, timecodes FROM lessons WHERE lesson_number=5"}'
```

Response has a `timecodes` JSONB array:

```json
[
  {"time": "00:00", "label": "Step 1 title", "description": "Step 1 description..."},
  {"time": "04:00", "label": "Step 2 title", "description": "Step 2 description"}
]
```

Each timecode = one step-frame. If timecodes < 5 — pad to 5. If > 5 — expand to 7+ frames.

## Step 1 — find/create board

```
mcp__miro__board_search_boards query="<course name>"
```

If no existing board:
```
mcp__miro__board_create name="<Course Name>" team_id=<id>
```

## Step 2 — create 6 frames

One `layout_create` without `moveToWidget`. Coordinates are board-absolute.

```
mcp__miro__layout_create
miro_url=https://miro.com/app/board/<BOARD_ID>=/
dsl=
f1 FRAME x=200 y=200    w=1920 h=1080 fill=#0f0e0b "Lesson 5 · Cover"
f2 FRAME x=200 y=1380   w=1920 h=1080 fill=#0f0e0b "Lesson 5 · Step 1"
f3 FRAME x=200 y=2560   w=1920 h=1080 fill=#0f0e0b "Lesson 5 · Step 2"
f4 FRAME x=200 y=3740   w=1920 h=1080 fill=#0f0e0b "Lesson 5 · Step 3"
f5 FRAME x=200 y=4920   w=1920 h=1080 fill=#0f0e0b "Lesson 5 · Step 4"
f6 FRAME x=200 y=6100   w=1920 h=1080 fill=#0f0e0b "Lesson 5 · Step 5"
```

Response includes frame URLs with `?moveToWidget=<FRAME_ID>`. Save the 6 frame IDs.

## Step 3 — fill TEXT, frame by frame

Use `moveToWidget=<frame_id>` — coordinates now **relative to the frame**. Max 12 items per call (HTTP 400 at >=14). Sequential per frame, parallelize across different frames.

### 3.1 — Cover frame

```
mcp__miro__layout_create
miro_url=https://miro.com/app/board/<BOARD>/?moveToWidget=<F1_ID>
dsl=
eb  TEXT x=300 y=140  w=780 align=left font=plex_mono   size=22 color=#c8a24a "LESSON 5 · 28 MIN"
t   TEXT x=300 y=300  w=780 align=left font=eb_garamond size=80 color=#fcfaf7 "Basic Prompting"
sub TEXT x=300 y=480  w=780 align=left font=plex_sans   size=24 color=#8a8275 "How to write prompts that work the first time."
h   TEXT x=300 y=640  w=780 align=left font=plex_mono   size=18 color=#c8a24a "WHAT WE COVER"
b1  TEXT x=300 y=720  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— Step 1 title"
b2  TEXT x=300 y=765  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— Step 2 title"
b3  TEXT x=300 y=810  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— Step 3 title"
b4  TEXT x=300 y=855  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— Step 4 title"
b5  TEXT x=300 y=900  w=780 align=left font=plex_sans   size=22 color=#fcfaf7 "— Step 5 title"
ft  TEXT x=300 y=1020 w=780 align=left font=plex_mono   size=14 color=#8a8275 "<your-domain>  ·  course name  ·  5 / 5"
```

### 3.2 — Step frame template

```
eb     TEXT x=300 y=140  w=780 align=left font=plex_mono   size=20-22 color=#c8a24a "STEP N · K MIN"
t      TEXT x=300 y=240  w=780 align=left font=eb_garamond size=56-64 color=#fcfaf7 "<Step title>"
sub    TEXT x=300 y=440  w=780 align=left font=plex_sans   size=22    color=#8a8275 "<lead-line, <=12 words>"
sec1_h TEXT x=300 y=540  w=780 align=left font=plex_mono   size=22    color=#c8a24a "SECTION HEADER"
sec1_b TEXT x=300 y=580  w=780 align=left font=plex_sans   size=22    color=#fcfaf7 "<body>"
sec2_h TEXT x=300 y=660  w=780 align=left font=plex_mono   size=22    color=#c8a24a "HEADER 2"
sec2_b TEXT x=300 y=700  w=780 align=left font=plex_sans   size=22    color=#fcfaf7 "<body>"
sec3_h TEXT x=300 y=780  w=780 align=left font=plex_mono   size=22    color=#c8a24a "HEADER 3"
sec3_b TEXT x=300 y=820  w=780 align=left font=plex_sans   size=22    color=#fcfaf7 "<body>"
pin    TEXT x=300 y=940  w=780 align=left font=plex_serif  size=20    color=#c8a24a "<dry statement <=8 words>"
```

### 3.2.1 — When content doesn't fit single-column (HARD RULE)

NEVER use a second column on the right. Right half = ONLY face-cam.

If a step has too much content:
- **Compact mode:** reduce bullet size to 18, spacing y+32 instead of y+42
- **Trim content:** combine related bullets, keep top-5 per section
- **Expand presentation:** split into 2 step-frames if content warrants it

### 3.3 — Large step (grid template)

For steps with many items (e.g. 6 antipatterns in a grid), split into two sequential calls:

**Call A (title + row 1, ~10 items):** eyebrow + title + subtitle + first 3 grid items
**Call B (row 2 + pin, ~8 items):** remaining 3 grid items + pin quote

Do not use `✕` (breaks API). Use `x` or `—` instead.

## Step 4 — final review

```
mcp__miro__layout_read miro_url=https://miro.com/app/board/<BOARD>=/
```

Verify 6 FRAMES + N TEXT items per frame. Report to user: frames ready, texts on left, right half empty, user does Convert to Slides manually.

## Step 5 — after Convert to Slides

API access to frames partially breaks after Convert to Slides — `layout_read` may return "Item not found". Make all edits **before** Convert to Slides.

## Debugging

| Symptom | Cause | Fix |
|---|---|---|
| Texts outside frame on left | Board-absolute coords without moveToWidget | `layout_update replace_all=true` to shift x |
| HTTP 400 on bulk create | >=14 items or `✕` symbol | Split into 2 calls, replace `✕` with `—` |
| HTTP 400 on single TEXT | Parallel race on same frame | Sequential per frame |
| Item not found on read | After Convert to Slides | Edits only via UI |
