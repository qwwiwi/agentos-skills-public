# Recipes — YouTube Thumbnail

## Palette (Claude Code)
- clay-orange `#D97757` (accent / l2 / logo / glow) — from `claude-code-default.svg`
- cream `#F3EEE3` (l1 headline)
- ink `#0A0806` (base)

## Fonts (yt-thumb.mjs `--font`, all Cyrillic-capable)
| key | character | good for |
|---|---|---|
| intertight | clean modern (default) | neutral, default |
| montserrat | geometric heavy | universal, safe |
| oswald | condensed tall | classic YouTube punch |
| russo | squarish techy | tech / Claude / code themes |
| unbounded | rounded display | modern, trendy |
| rubik | friendly heavy | softer brands |
| manrope | clean grotesk | minimal |
Long lines (e.g. "ДЛЯ БИЗНЕСА") → drop `--fs`: oswald ~132, montserrat ~106, russo ~96, unbounded ~82.

**Serif (Anthropic/Copernicus-style headline) — added 2026-06-25:** `sourceserif` (closest to
Copernicus, literary serif), `spectral`, `ptserif`, `playfair` — all Cyrillic-capable, free.
NOTE: Anthropic's REAL brand fonts are **Copernicus** (display serif, headlines) + **Styrene A/B**
(sans, UI) by Commercial Type — COMMERCIAL, not installable for free, and likely **no Cyrillic**
(Latin brand) so Russian headlines won't set even with the files. Use the free serif lookalikes for
the "Claude/Anthropic" headline look in Russian; only use real Copernicus/Styrene if you
provides licensed .otf/.ttf AND the text is Latin.

## RU YouTube thumbnail font research (2026-06-25)
Principles: heavy weight (800-900), ALL CAPS, ≤2-4 words, condensed for long words, high contrast +
shadow/stroke, no decoration (read in ~1s). **Cyrillic is mandatory** — the iconic Latin thumbnail
fonts Impact / Bebas Neue / Anton have NO Cyrillic (only clones / "Bebas Neue Cyrillic" variant).
- Free + Cyrillic (in `--font`): Oswald (condensed, best for long words), Montserrat 900 (premium
  universal), Rubik 900, Unbounded 800, Russo One (techy), Alfa Slab One (slab, "tech" — add if needed).
- Serif/Anthropic look: Source Serif 4, Spectral.
- Popular downloadable RU thumbnail fonts (not Google): Molot, Obelix Pro, Gagalin, Phenomena (punchy).
- Premium Cyrillic foundries: TypeType (TT Travels Next, TT Norms) — RU studio, gold standard; paid.
- **Local/premium font files** (composer `--fontfile path.ttf`): bundled in `assets/fonts/` —
  `BebasNeueCyrillic.ttf` (iconic tall condensed, OFL, Cyrillic ✓) and `Molot.otf` (bold RU display,
  OFL, Cyrillic ✓). Both free for commercial use. Bebas → `--fs ~150` (condensed), Molot → `--fs ~116`.
  Verify any new font's Cyrillic by rendering "АГЕНТЫ" (tofu = no Cyrillic). gpt-image can NOT be
  forced to a specific premium font — use engine C (no-text base + `--fontfile` overlay).
- Avoid gaming/decorative (CSGO, STALKER, Minecraft) unless gaming channel.
Recommendation for an AI / coding channel: punch = Oswald or Montserrat 900; Anthropic look =
Source Serif 4; tech accent = Russo One / Unbounded. Sources: manypixels, figma, typetype.org, pixelbox.ru.

## gpt-image-2 prompts (codex-image run.sh "prompt" high landscape [refs])
**Likeness:** give 4 close frontal face crops (different outfits) — 1 wide shot is not enough.
Crop: `ffmpeg -i pick.png -vf "crop=1300:1300:430:760,scale=720:720" faceref.jpg` (from vertical 2160×3840).

**Full-gen (engine A):**
> Create a high-CTR YouTube thumbnail, 16:9. The person MUST be the exact same man in the reference photos — preserve his real face, round glasses, hairstyle and likeness precisely, do NOT beautify. Show him chest-up on the RIGHT in a white t-shirt, energetic, looking at camera. Background: dark charcoal + warm clay-orange glow hex D97757, Anthropic Claude / Claude Code style — glowing terminal code lines, an orange asterisk spark, connected AI-agent nodes, warm bokeh. LEFT: two-line bold text 'АГЕНТЫ' cream + 'ДЛЯ БИЗНЕСА' clay-orange, eyebrow 'CLAUDE CODE' orange mono. Spell Russian exactly. High contrast, no watermark.

**No-text base (engine C — then overlay text via yt-thumb):** same but →
> ...with NO TEXT at all. Keep the LEFT HALF darker, clean and empty (space for text later). ABSOLUTELY NO text, words, letters, numbers or logo anywhere.

**Gotchas:** Cyrillic usually renders clean; the `→` arrow garbles → use "to"/"до". Output ~1672×941 → finalize.

## Highlight-box style ("AI LABS" — black bg + marker boxes) — scripts/yt-boxes.mjs
Faceless-friendly flat style: solid dark bg + bold sans + KEY WORDS in yellow/white highlight boxes
(black text) + optional real face cutout + brand icon. Perfect Cyrillic (text is ours, not the model's).
```bash
node scripts/yt-boxes.mjs --eyebrow "CLAUDE CODE" --l1 "[[АГЕНТЫ]]" --l2 "ДЛЯ БИЗНЕСА" \
  --face cutouts/13.png --icon .../claude-code-default.svg --font inter --fs 124 --out out.png
```
Markup in `--l1/--l2`: `[[word]]`=yellow box, `<<word>>`=white box, plain=white text. Fonts: inter
(default, Helvetica-like, Cyrillic), montserrat, hanken, manrope; or `--fontfile`. Yellow #EEFF00.
Reference: AI LABS channel (@ailabs-393) — covers in `_assets/yt/refcovers/`. This style is the best
fit for a repeatable Claude-Code video SERIES (cheap, instant, on-brand). GPT-image can also hit this
style with 2 style-example refs + face refs, and rendered clean Cyrillic in the box (2026-06-25).

## Finalize to exact 1920×1080
```bash
ffmpeg -y -i in.png -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" out.png
```

