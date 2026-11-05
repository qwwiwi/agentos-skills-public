---
name: youtube-thumbnail
description: >-
  Generate premium, high-CTR YouTube thumbnails (1920x1080) in a consistent series
  style — dark background, clay-orange accent (#D97757), the author's real face, a
  punch headline, and a brand logo. Use this WHENEVER the user asks for a YouTube
  cover/обложка/thumbnail, wants a face pulled from a video onto a cover, wants
  to "play with the font" on a cover, or wants a thumbnail in a fixed brand style.
  Default pipeline (MANDATORY): gpt-image-2 with EXACTLY 5 references — two real face
  photos + two reference covers + one brand logo — to copy the reference style
  with the real large face. Deterministic fallback: scripts/yt-boxes.mjs (no GPT).
---

# YouTube Thumbnail Generator

Make a 1920×1080 thumbnail that is cohesive, catchy, and readable at small size.
Default palette: clay-orange `#D97757`, cream `#F3EEE3`, near-black `#0A0806` (change it to
your brand in the prompt and in the scripts' constants). Logos: any PNG, or an official SVG
from the `logo-company` skill rasterized with `scripts/rasterize-logo.mjs`.

Working dir for a job: `~/yt-covers/` (or any folder you choose) with subfolders
`facerefs/` (approved face photos), `refcovers/` (style examples), `picks/`, `cutouts/`, `out/`.

## Engine — primary + fallback (no improvising)

**Primary (MANDATORY, default for every cover):** GPT full-generation via gpt-image-2 using EXACTLY 5
references — two real face photos, two reference covers, one brand logo — see **MANDATORY
pipeline** below. This is what produces the dark + accent glow + yellow-box look with a real LARGE
face and crisp Russian text.

**Fallback only:** `scripts/yt-boxes.mjs` (no GPT, fully deterministic text) — use ONLY when the user
asks for exact deterministic text control, or GPT/Codex is unavailable. `yt-thumb.mjs` / `cutout.py` are
building blocks for that fallback.

Steps 1–5 below are the building blocks; the **MANDATORY pipeline** section is the exact order to run them.

## Pipeline

### 1. Face from video
```bash
# probe + grab evenly-spaced frames (ffmpeg -ss BEFORE -i = fast seek)
ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4
ffmpeg -y -ss <sec> -i in.mp4 -frames:v 1 -q:v 2 frame.png
```
If two face photos are already provided, use them directly. If only a video is given: make a numbered
contact sheet (tile filter), send it, and STOP until exactly two frame numbers are chosen — before any GPT
generation. Save the two final close crops as `facerefs/face1.jpg` and `facerefs/face2.jpg`.
ZSH GOTCHA: zsh does NOT glob `*` from a variable (bash does) — hardcode timestamps or list filenames explicitly.

### 2a. Real cutout (fallback engine) — rembg
```bash
<skill>/.venv/bin/python scripts/cutout.py picks/13.png cutouts/13.png
```
Vertical phone video = 2160×3840 → resize to h≤1280 before cutout (cutout.py does it).
rembg model u2net_human_seg, Python API (NOT CLI). venv: see Setup.

### 2b. Face refs for GPT — close crops
Crop tight frontal faces (better likeness than one wide shot). Crop coords are FRAME-SPECIFIC — re-derive
`crop=W:H:X:Y` per frame; the values below are an example for one frame, do not reuse blindly:
```bash
ffmpeg -y -i picks/13.png -vf "crop=1300:1300:430:760,scale=720:720" facerefs/face1.jpg
```

### 3. Scene / base via gpt-image-2
`run.sh "prompt" high landscape [ref1..ref5]` — the `codex-image` skill, OAuth subscription (no API key).
Refs as input_image (≤5). Cyrillic in text renders CLEAN usually, but the **→ arrow
garbles** — write "to"/"до". For a no-text base, prompt for **NO text, left half empty**.
Prompt core: "exact same person as in the reference photos, preserve real face/glasses/hair,
do NOT beautify; right side; dark charcoal + clay-orange #D97757 glow, terminal code,
AI-agent nodes; high contrast; no watermark".

### 4. Compose text + logo (fallback engine) — scripts/yt-thumb.mjs
```bash
node scripts/yt-thumb.mjs --scene /abs/SCENE.png --face /abs/cutout.png \
  --logo /abs/logo.svg \
  --eyebrow "CLAUDE CODE" --l1 "АГЕНТЫ" --l2 "ДЛЯ БИЗНЕСА" \
  --font oswald --fs 104 --faceside right --out /abs/out.png
```
- `--scene` ABSOLUTE path (code does `file://`+path; relative → black bg).
- `--face` optional (omit when the face is baked into the GPT base).
- `--l2` renders in the accent color. `--faceside right|left` (text goes opposite, scrim there).
- `--fs` font size (default 150; long lines like "ДЛЯ БИЗНЕСА" → ~104).
- `--font`: intertight (default) · montserrat · oswald · russo · unbounded · rubik · manrope
  (all Cyrillic-capable, thumbnail-strong). "Play with font" = render several.
- Logo PNG from SVG: `node scripts/rasterize-logo.mjs logo.svg out.png 600`.

### 5. Finalize 1920×1080
gpt-image outputs ~1536×1024/1672×941 → crop/scale to exactly 1920×1080:
```bash
ffmpeg -y -i in.png -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" out.png
```
QA: `ffmpeg -y -i out.png -vf scale=360:-1 qa-360.png` — pass ONLY if the full Russian headline is spelled
exactly, the KEYWORD sits inside a yellow box, and every word is readable. If not: regenerate once; still
bad → fall back to `scripts/yt-boxes.mjs`.

## MANDATORY pipeline — how this skill makes a cover (deterministic)

This is the strict, non-negotiable function of the skill. Every cover follows EXACTLY these steps — do not
prompt a scene from scratch and do not improvise the inputs. SHOW gpt-image the style with example covers
and let it copy it, with the real face large.

**Steps (always, in order):**
1. **Two face photos of the author** — cut from a video (steps 1 / 2b) or otherwise sourced. Clear, frontal, large.
2. **Two reference covers + one brand logo** — the style examples to copy + the logo used on the cover.
3. **One prompt** — copy the reference style, keep the real face LARGE, set the exact headline.
4. **Load all 5 into gpt-image-2** (codex-image, OAuth) → it outputs the cover in-style with the face + text.
5. **Finalize to 1920×1080** (ffmpeg, above).

The point: the cover must look like the reference AND carry the real face AND the chosen headline — that is
only guaranteed by feeding examples + photos + logo together, not by describing the style in words.

**Upload to gpt-image — STRICTLY these 5 refs:**
1–2. TWO live face photos of the person — **ALWAYS from one canonical face library** (`facerefs/`:
     pre-cut frames from one good studio video, each outfit as a separate file). **NEVER improvise face
     refs from ad-hoc phone or carousel photos** — a random photo gives a wrong face/likeness.
     Pick two clear frontal ones; crop tighter only if needed.
     **Eyes rule:** only frames with fully open eyes and a direct gaze. The prompt adds
     «eyes fully open, gaze exactly as in the reference, do not redraw the face». Move rejected
     blink / squint / side-gaze frames into `facerefs/_rejected/` and never use them: one half-closed
     eye in a reference is copied onto every cover.
3–4. TWO reference covers in the target style. If the user gives exact target covers, use those two.
     Otherwise use two fixed files from `refcovers/` (keep 10–15 examples of the one style you copy,
     e.g. dark background + yellow highlight box) so the whole series stays consistent.
5. ONE brand logo as PNG (e.g. `logos/product-logo.png`).

**Cover about ANOTHER brand (OpenAI, Gemini, etc.) — keep your style, swap the mark:**
The layout + your face IS your style — reuse it for any topic. To brand it for a different company:
(a) get its logo SVG from `logo-company` (`find-logo.sh openai default`), (b) rasterize → PNG
(`node scripts/rasterize-logo.mjs <svg> <out.png> 600`), (c) use it as ref #5 INSTEAD of your usual logo,
(d) in the prompt say EXPLICITLY: «do NOT draw the <YOUR USUAL MARK>; instead prominently feature the
<BRAND> logo (from the logo reference) near top center» — else gpt-image copies the mark it sees on the
two reference covers. Keep refs #3–4 for the STYLE.

**Prompt core — the FACE MUST BE LARGE:**
> Design a 16:9 YouTube thumbnail that copies the EXACT visual style of the reference cover images: solid
> near-black background, subtle terminal-window outlines + code texture, a heavy bold headline with a
> bright YELLOW highlight box on the key word, brand label top-left.
> Use the person from the face photos — the REAL face/glasses/hair, do NOT beautify — shown LARGE and
> close-up on the RIGHT, sharp, looking at camera. Eyes fully open, gaze exactly as in the reference,
> do not redraw the face. Headline left: '<HEADLINE>' with '<KEYWORD>' in a
> yellow box. Render the Russian text exactly as written. Crisp, high-contrast, no watermark.

Run (`run.sh` is NOT on PATH — use the full path; ALL refs absolute):
```bash
~/.claude/skills/codex-image/scripts/run.sh "$PROMPT" high landscape \
  /abs/facerefs/face1.jpg /abs/facerefs/face2.jpg \
  /abs/refcovers/01.jpg /abs/refcovers/02.jpg \
  /abs/logos/product-logo.png
```
Then finalize to 1920×1080 (step 5). The reference covers make gpt render crisp Cyrillic IN-STYLE (no garble) —
this is why we feed examples instead of describing the style.

With the current `codex-image` skill you can do the same through its brief: `brief.py init brief.json --type
youtube-cover`, a registry preset with these 5 refs, `brief.py check`, `brief.py prompt` (it adds the eyes
constraint itself and refuses refs from `_rejected/`).

**Deterministic fallback (your own text, no gpt):** `scripts/yt-boxes.mjs` — solid dark bg; markup inside
`--l1/--l2`: `[[word]]`=yellow box, `<<word>>`=white box, plain=white text; real rembg face cutout (right);
brand icon; `--eyebrow`. Perfect Cyrillic.
```bash
cd ~/.claude/skills/youtube-thumbnail
node scripts/yt-boxes.mjs --l1 "[[АГЕНТЫ]] ДЛЯ" --l2 "YOUTUBE" --eyebrow "CLAUDE CODE" \
  --face /abs/cutout.png --icon /abs/logos/product-logo.png --font inter --out /abs/out.png
```

## Setup (once)
```bash
cd ~/.claude/skills/youtube-thumbnail
python3 -m venv .venv && .venv/bin/pip install rembg onnxruntime pillow
npm i playwright && npx playwright install chromium   # if chromium-headless-shell missing
```
gpt-image setup: install the `codex-image` skill and Codex CLI (`npm install -g @openai/codex`), then
`codex login` (or `codex login --device-auth`). The `codex-image` `run.sh` bootstraps its own Python venv on first run.
Also needed: `ffmpeg` / `ffprobe` on PATH.

## References
- `references/recipes.md` — prompts, palette, font notes.
