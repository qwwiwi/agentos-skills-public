# Recipes — YouTube Thumbnail

## Palette (default)
- clay-orange `#D97757` (accent / l2 / logo / glow)
- cream `#F3EEE3` (l1 headline)
- ink `#0A0806` (base)

## Fonts (yt-thumb.mjs `--font`, all Cyrillic-capable)
| key | character | good for |
|---|---|---|
| intertight | clean modern (default) | neutral, default |
| montserrat | geometric heavy | universal, safe |
| oswald | condensed tall | classic YouTube punch |
| russo | squarish techy | tech / code themes |
| unbounded | rounded display | modern, trendy |
| rubik | friendly heavy | softer brands |
| manrope | clean grotesk | minimal |
Long lines (e.g. "ДЛЯ БИЗНЕСА") → drop `--fs`: oswald ~132, montserrat ~106, russo ~96, unbounded ~82.

**Serif headline:** `sourceserif` (literary serif), `spectral`, `ptserif`, `playfair` — all
Cyrillic-capable, free. Commercial brand fonts usually have no Cyrillic: for Russian headlines use
the free lookalikes.

## RU YouTube thumbnail font notes
Principles: heavy weight (800-900), ALL CAPS, ≤2-4 words, condensed for long words, high contrast +
shadow/stroke, no decoration (read in ~1s). **Cyrillic is mandatory** — the iconic Latin thumbnail
fonts Impact / Bebas Neue / Anton have NO Cyrillic (only clones / a "Bebas Neue Cyrillic" variant).
- Free + Cyrillic (in `--font`): Oswald (condensed, best for long words), Montserrat 900 (premium
  universal), Rubik 900, Unbounded 800, Russo One (techy).
- Serif look: Source Serif 4, Spectral.
- **Local font files**: pass any licensed `.ttf/.otf` with `--fontfile path.ttf`. Check the licence
  yourself before you ship a font. Verify Cyrillic by rendering "АГЕНТЫ" (tofu = no Cyrillic).
  gpt-image can NOT be forced to a specific font — for an exact font generate a no-text base and
  overlay the text with `yt-thumb.mjs --fontfile`.
- Avoid gaming/decorative fonts unless it is a gaming channel.
Recommendation for an AI / coding channel: punch = Oswald or Montserrat 900; serif look =
Source Serif 4; tech accent = Russo One / Unbounded.

## gpt-image-2 prompts (codex-image run.sh "prompt" high landscape [refs])
**Likeness:** give close frontal face crops — 1 wide shot is not enough.
Crop: `ffmpeg -i pick.png -vf "crop=1300:1300:430:760,scale=720:720" faceref.jpg` (from vertical 2160×3840).
**Eyes:** only frames with fully open eyes and a direct gaze; add to the prompt
"eyes fully open, gaze exactly as in the reference, do not redraw the face".

**Full generation:**
> Create a high-CTR YouTube thumbnail, 16:9. The person MUST be the exact same person as in the reference photos — preserve the real face, glasses, hairstyle and likeness precisely, do NOT beautify. Eyes fully open, gaze exactly as in the reference. Show the person chest-up on the RIGHT, energetic, looking at camera. Background: dark charcoal + warm clay-orange glow hex D97757 — glowing terminal code lines, connected AI-agent nodes, warm bokeh. LEFT: two-line bold text 'АГЕНТЫ' cream + 'ДЛЯ БИЗНЕСА' clay-orange, eyebrow 'CLAUDE CODE' orange mono. Spell Russian exactly. High contrast, no watermark.

**No-text base (then overlay text via yt-thumb):** same but →
> ...with NO TEXT at all. Keep the LEFT HALF darker, clean and empty (space for text later). ABSOLUTELY NO text, words, letters, numbers or logo anywhere.

**Gotchas:** Cyrillic usually renders clean; the `→` arrow garbles → use "to"/"до". Output ~1672×941 → finalize.

## Highlight-box style (black bg + marker boxes) — scripts/yt-boxes.mjs
Faceless-friendly flat style: solid dark bg + bold sans + KEY WORDS in yellow/white highlight boxes
(black text) + optional real face cutout + brand icon. Perfect Cyrillic (text is yours, not the model's).
```bash
node scripts/yt-boxes.mjs --eyebrow "CLAUDE CODE" --l1 "[[АГЕНТЫ]]" --l2 "ДЛЯ БИЗНЕСА" \
  --face cutouts/13.png --icon /abs/logo.svg --font inter --fs 124 --out out.png
```
Markup in `--l1/--l2`: `[[word]]`=yellow box, `<<word>>`=white box, plain=white text. Fonts: inter
(default, Helvetica-like, Cyrillic), montserrat, hanken, manrope; or `--fontfile`. Yellow #EEFF00.
This style is the best fit for a repeatable video SERIES (cheap, instant, on-brand). gpt-image can also
hit this style with 2 style-example refs + face refs, and renders clean Cyrillic in the box.

## Finalize to exact 1920×1080
```bash
ffmpeg -y -i in.png -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" out.png
```
