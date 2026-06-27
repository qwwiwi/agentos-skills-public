---
name: youtube-thumbnail
description: >-
  Generate premium, high-CTR YouTube thumbnails (1920x1080) — your real face from
  video frames, a punchy headline, a brand logo, on a dark high-contrast scene.
  Use this WHENEVER you need a YouTube cover/обложка/thumbnail, want a face pulled
  from a video onto a cover, want to "play with the font" on a cover, or want a
  thumbnail in a specific brand palette. Three engines: (A) GPT full-generation via
  gpt-image-2 with face+logo reference photos; (B) Compose — real rembg face cutout +
  scene + text via Playwright; (C) Hybrid — GPT no-text base + compose text for exact
  font control.
---

# YouTube Thumbnail Generator

Make a 1920×1080 thumbnail that is cohesive, catchy, and readable at small size:
your real face + a 2–4 word headline + a brand logo on a dark, high-contrast scene.

Pick your own brand palette. The examples below use a clay-orange accent
(`#D97757`) on near-black (`#0A0806`) with a cream headline (`#F3EEE3`) — swap for yours.

Working dir for a job (frames, cutouts, scenes, outputs): keep it under the skill, e.g.
`~/.claude/skills/youtube-thumbnail/work/`.

## Three engines — pick by need

| Engine | Face | Text control | Use when |
|---|---|---|---|
| **A. GPT full-gen** | gpt-image redraws likeness from refs | font baked by the model | fast, cohesive, AI-rendered face is fine |
| **B. Compose** | real cutout (rembg) — exact likeness | full font/layout control | authentic real face, repeatable series |
| **C. Hybrid** | GPT no-text base (face+scene) + compose text | full font control | you like the GPT look but want the font exact |

Likeness tip: GPT needs **4+ close, frontal face refs** to actually look like the person.
"Play with the font" → use **B or C** so the font is yours, not the model's.

## Recommended path — examples + photos → GPT (reliable style match)

The most reliable way to hit a specific cover style (e.g. solid dark bg + an accent asterisk/spark + a
bright highlight box on a key word) is to **show gpt-image the style with example covers** instead of
describing it in words. Feed up to 5 references:

- **Two face photos** of the person (close frontal crops — see step 1 / 2b).
- **Two reference covers** in the target style — keep your style examples in `references/refcovers/`.
- **One brand logo** used on the cover.

Prompt: *"copy the EXACT visual style of the reference cover images (background, accent graphic, terminal
texture, heavy headline with a bright highlight box on the key word, brand label); use the person from the
face photos — real face, shown LARGE and close-up on the right; headline `<HEADLINE>` with `<KEYWORD>` in a
highlight box; render the text exactly as written; high contrast, no watermark."* Then finalize (step 5).

Feeding examples is what makes the model reproduce the box style AND keep the text crisp. For fully
**deterministic text** instead, use `scripts/yt-boxes.mjs` — solid dark bg, markup `[[word]]`=accent box /
`<<word>>`=white box / plain=white text, real face cutout, brand icon:
```bash
node scripts/yt-boxes.mjs --l1 "[[KEYWORD]] REST" --l2 "SECOND LINE" --eyebrow "BRAND" \
  --face /abs/cutout.png --icon /abs/logo.png --font inter --out /abs/out.png
```

## Pipeline

### 1. Face from video
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4
ffmpeg -y -ss <sec> -i in.mp4 -frames:v 1 -q:v 2 frame.png   # -ss BEFORE -i = fast seek
```
Grab evenly-spaced frames, build a numbered contact sheet (ffmpeg `tile` filter), and let the
user pick by number. ZSH gotcha: zsh does NOT word-split a `*` glob from a variable — hardcode
timestamps or list filenames explicitly.

### 2a. Real cutout (engine B/C) — rembg
```bash
.venv/bin/python scripts/cutout.py picks/13.png cutouts/13.png
```
Vertical phone video (2160×3840) → resize to height ≤1280 before cutout (cutout.py handles it).
Model `u2net_human_seg` via the rembg Python API.

### 2b. Face refs for GPT (engine A) — close crops
Tight frontal crops beat one wide shot; give ~4 different outfits/angles:
```bash
ffmpeg -y -i picks/13.png -vf "crop=1300:1300:430:760,scale=720:720" facerefs/13.jpg
```

### 3. Scene / base via gpt-image-2 (engine A/C)
Use any **gpt-image-2** generator (OpenAI image API, or a Codex-OAuth wrapper) that accepts
input reference images (≤5): pass the face crops (+ logo). Cyrillic text renders cleanly in most
cases, but a literal **→ arrow garbles** — write "to"/"до" instead. For engine C, prompt for
**NO text, left half empty** so you can compose text yourself.

Prompt core: "exact same person as in the reference photos, preserve the real face/glasses/hair,
do NOT beautify; subject on the right; dark charcoal background + a brand-accent glow; subtle
terminal/code texture; high contrast; no watermark".

### 4. Compose text + logo (engine B/C) — scripts/yt-thumb.mjs
```bash
node scripts/yt-thumb.mjs --scene /abs/SCENE.png [--face /abs/cutout.png] \
  --logo /abs/logo.svg \
  --eyebrow "EYEBROW" --l1 "LINE ONE" --l2 "LINE TWO" \
  --font oswald --fs 104 --faceside right --out out.png
```
- `--scene` ABSOLUTE path (code does `file://`+path; a relative path → black bg).
- `--face` optional (omit for engine C — the face is baked into the GPT base).
- `--l2` renders in the accent color. `--faceside right|left` (text goes opposite, with a scrim).
- `--fs` font size (default 150; long lines like a 10+ char word → ~104).
- `--font`: intertight (default) · montserrat · oswald · russo · unbounded · rubik · manrope · sourceserif · spectral (all Cyrillic-capable, thumbnail-strong). "Play with the font" = render several.
- Logo PNG from SVG: `node scripts/rasterize-logo.mjs logo.svg out.png 600`. Supply your own logo.

### 5. Finalize 1920×1080
gpt-image outputs ~1536×1024 → crop/scale to exactly 1920×1080:
```bash
ffmpeg -y -i in.png -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" out.png
```
QA: `ffmpeg -y -i out.png -vf scale=360:-1 qa-360.png` — pass only if the full headline is spelled exactly,
the key word sits inside its highlight box, and every word is readable at small size. If not: regenerate
once, then fall back to `scripts/yt-boxes.mjs` for exact text.

## Setup (once)
```bash
cd ~/.claude/skills/youtube-thumbnail
python3 -m venv .venv && .venv/bin/pip install rembg onnxruntime pillow   # engine B/C cutout
npm i playwright && npx playwright install chromium                        # text compositor
```
For engine A/C you also need access to a gpt-image-2 generator (OpenAI image API key, or a
Codex-OAuth image wrapper).

## References
- `references/recipes.md` — palette, font notes (per-font sizing for long words), prompt patterns.
