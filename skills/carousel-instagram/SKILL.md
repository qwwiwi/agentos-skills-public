---
name: carousel-instagram
description: >-
  Generate Instagram carousels: 1080x1350 PNG slides from text (headline + body)
  and user photos, laid out in HTML/CSS and rendered headless via Playwright.
  Full design system baked in (Montserrat; cover/content/CTA card roles; calculated
  photo height; text-safe zones over faces; hyphen-only punctuation). Coral default
  palette, fully restylable to any brand (e.g. EdgeLab lime). Use WHENEVER you need
  a carousel for an Instagram post, want to lay out post slides, or turn a text +
  photos into a swipeable post. Triggers: "make a carousel", "carousel", "carousel
  post", "post slides", "slides for a post", "карусель", "слайды для поста",
  "пост-карусель", carousel/carousel. NOT for: single covers, reels, stories.
---

# Instagram Carousel

Generates 1080x1350px PNG carousel slides for Instagram from text and photos.
Each slide is a self-contained HTML file, rendered headless to PNG. This skill
drives an LLM (Opus or GPT) to plan and author the slide HTML; the design system
below is the value - keep it intact.

The default palette is coral (`#D97757`) on dark (`#1C1510`). It is fully
restylable to any brand - swap the color tokens in section 2 (for example, an
EdgeLab lime accent) and the layout rules stay the same.

## 0. Setup (once)

```bash
npm i playwright && npx playwright install chromium
```

That is all the renderer needs. Slides are plain HTML that load Montserrat from
Google Fonts, so an internet connection is required at render time.

## 1. Workflow

1. **Collect inputs** - slide text (headline + body) and photos from the user.
   Put photos in a local `./photos/` dir and reference them as `file://` URLs.
2. **Plan each slide** - determine card role (cover / content / CTA), layout,
   photo placement, and calculate photo/text heights (sections 3-4).
3. **Generate HTML** - one file per slide, named `slide_01.html`, `slide_02.html`,
   ... in a slides dir (for example `./slides/`).
4. **Render to PNG** - `node scripts/render.mjs ./slides ./out`. Each
   `slide_*.html` is opened at 1080x1350, fonts awaited, screenshotted to
   `./out/slide_NN.png`.
5. **QA** - run the pre-render checklist (section 7) against each PNG. A clipped
   or face-covered slide is a rejected slide - fix and re-render.
6. **Deliver** - hand over the finished PNGs (upload order = slide order).

---

## 2. Design System

### Colors
```
Background:       #1C1510
Accent:           #D97757  (coral)
Text primary:     #FFFFFF
Text secondary:   rgba(255,255,255,0.65)
Decorative lines: rgba(217,119,87,0.35)
```

To restyle to another brand, swap the accent and background tokens (for example,
an EdgeLab lime accent on the same dark base) and keep every layout rule below.

### Typography
- **Font**: Montserrat - load from Google Fonts
- **Headline**: ExtraBold 800, 64-80px, letter-spacing: -0.04em
- **Body**: Regular 400, 36-42px, letter-spacing: -0.04em
- **CTA**: Bold 700, 52-64px, letter-spacing: -0.04em

### Decorative elements
Thin geometric lines only - corner L-shapes, horizontal accent lines, diagonal
lines. No illustrations, icons, or logo. Max 3 decorative elements per card.
Stroke: 1-2px, color: `rgba(217,119,87,0.35)`.

### Punctuation
Always short hyphen (-). Never em-dash or en-dash. Applies everywhere: headlines,
body, CTA.

---

## 3. Card Types

### Card 1 - Cover (hook)
- **Photo**: always present, always a portrait/face photo. User provides it.
- **Text**: headline only, max 3 lines. No body text.
- **Layout**: choose based on photo or user preference - see Layout A/B/C below.

### Cards 2-5(6) - Content slides
- **Photo**: optional. User provides if needed.
- **Text**: headline + body (2-4 lines).
- **Layout**: photo top, text bottom. See photo sizing rules in section 4.

### Last card - CTA
- **Photo**: never.
- **Text**: call to action (large accent text) + sub-text + keyword box.
- **Layout**: centered vertically, text only.

---

## 4. Layout Rules

### Cover layouts (Card 1)

**Layout A - photo full background, text at bottom**
Use when: wide/full-body/lifestyle shot, subject not filling the whole frame.
- Photo: `position: absolute; inset: 0; object-fit: cover; object-position: top center`
- Gradient: `linear-gradient(to top, rgba(28,21,16,0.97) 0%, rgba(28,21,16,0.88) 20%, rgba(28,21,16,0.30) 48%, transparent 58%)`
- Gradient becomes transparent before shoulders - face stays fully visible and undarked
- Text zone: bottom 35-40% of card (470-540px), padding 80px

**Layout B - photo top, text bottom (hard split)**
Use when: tight portrait, face fills most of the frame.
- Photo: top 580px, `object-fit: cover; object-position: top center`
- Separator: 2px accent line `rgba(217,119,87,0.5)`
- Text zone: remaining 768px, padding 80px

**Layout C - text top, photo bottom**
Use when: user explicitly requests text at top.
- Text zone: top 770px, padding 80px
- Photo: bottom 578px, `object-fit: cover`

**Choosing layout when user doesn't specify:**
- Wide/full-body/lifestyle photo -> Layout A
- Tight portrait (face fills frame) -> Layout B
- Unsure -> ask

### Content slide layout (Cards 2-5)

Photo always on top, text always on bottom.

**Photo height is calculated - never hardcoded:**
1. Calculate text zone height:
   - padding top: 64px
   - accent-line: 3px + margin 32px = 35px
   - headline: (lines x font-size x line-height) + margin 28px
   - body: (lines x font-size x line-height)
   - padding bottom: 80px
2. Minimum text zone: **480px**. If calculated height is less - increase font-size or line-height.
3. Photo height = 1350px - text zone - 2px separator

Example: 1-line headline (68px) + 4 body lines (37px x 1.55) = text zone ~511px = photo ~837px.

### Safety rules - face/body (all cards with photos)
- Text NEVER overlaps face, neck, or shoulders
- Safe buffer: 80px below the lowest shoulder
- In Layout A: gradient must be fully transparent before chest/shoulder level
- When in doubt: use hard split (Layout B)

### Headlines
Break to next line only if the headline genuinely doesn't fit on one line.
At 68px Montserrat ExtraBold with 80px padding: ~18-20 characters fit per line.
Never break for aesthetics.

### Spacing
- Padding from card edges: 80px on all sides
- Max gap between text elements: 40px
- If text zone feels empty: increase line-height first, then font-size

### Text overflow - CRITICAL
Theoretical height calculation can be wrong - text wraps to more lines than expected.
Always add **+80px overflow safety margin** to calculated text zone height.

If body is long (4+ lines, or 2 paragraphs):
- Use lower end of font range (body: 36px, headline: 64-68px)
- Or shorten the text to fewer lines

Rule: when in doubt - make text zone larger and photo smaller, never the reverse.
Clipped text = rejected card.

---

## 5. HTML Structure

Every slide is a self-contained HTML file:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;800&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 1080px; height: 1350px; overflow: hidden;
      background: #1C1510;
      font-family: 'Montserrat', sans-serif;
    }
  </style>
</head>
<body>
  <!-- slide content -->
</body>
</html>
```

Adapt per card type:
- **Cover Layout A**: absolute photo + gradient div + absolute text div at bottom
- **Cover Layout B / Content**: flex column - photo zone (calculated px) + separator (2px) + text zone (flex: 1)
- **CTA**: flex column, justify-content: center, no photo

### Working with photos
- Keep source photos in a local `./photos/` dir
- Reference as: `file:///abs/path/to/photos/filename.jpg` (absolute `file://` URL)
- Always use `object-fit: cover` on photo images

---

## 6. Rendering

```bash
node scripts/render.mjs ./slides ./out
```

Renders each `slide_*.html` (sorted) at 1080x1350px via Playwright chromium,
saves each as `./out/slide_NN.png`. It waits for `document.fonts.ready` so
Montserrat is loaded before the screenshot, then a short settle for paint.

---

## 7. Pre-render Checklist

Before generating each HTML file:
- [ ] Photo height calculated from text zone, not hardcoded
- [ ] Text zone height includes +80px overflow safety margin
- [ ] Text does not overflow card bottom - add `overflow: hidden` to text zone
- [ ] Text does not overlap face / neck / shoulders
- [ ] Headline on one line unless it genuinely doesn't fit
- [ ] No em-dashes anywhere - only hyphens (-)
- [ ] Padding 80px from all edges
- [ ] Max gap between text elements 40px
- [ ] No more than 3 decorative elements
- [ ] Font sizes: headline 64-80px, body 36-42px

---

## 8. Common Mistakes

- Hardcoding photo height - always calculate from text zone
- Forgetting +80px overflow margin - text gets clipped at bottom
- Text zone without `overflow: hidden` - content bleeds outside card
- Text on face / neck / shoulders
- Breaking headline when it fits on one line
- Em-dash anywhere in text
- Gap between text elements > 40px
- Logo, @handle, or any branding
- Gradient background (solid #1C1510 only, except Layout A overlay)
- Any font other than Montserrat
