---
name: present
description: "Generate beautifully formatted HTML presentations with a dark theme. Triggers: /present, 'create presentation', 'visualize', 'make HTML'. Accepts any content (lesson, report, data, plan, comparison, roadmap) and produces a standalone HTML file."
---

# Present — HTML Visualization

## When to use
- User writes `/present` or asks to format something visually
- Need to visualize data, a lesson, report, plan, or comparison
- Request for an HTML file to view in a browser

## Process

1. **Determine content type** — lesson, report, data, plan, comparison, roadmap
2. **Gather content** — from the conversation, files, or generate it
3. **Create HTML** using the design system below
4. **Save** as `present-{topic}.html` in your working directory
5. **Send** to the user (as a document attachment or file)

## Design System

### Colors (dark theme — default)
```
--el-bg: #141416
--el-text: #ffffff
--el-text-muted: #a1a1aa
--el-card-bg: rgba(255,255,255,0.06)
--el-card-border: rgba(255,255,255,0.1)
--el-accent: #c9a44a (gold)
--el-accent-dim: rgba(201,164,74,0.15)
--el-code-bg: rgba(255,255,255,0.08)
--el-divider: rgba(255,255,255,0.1)
--el-error: #ef4444
--el-success: #22c55e
```

### Fonts
- Headings: `'Playfair Display', Georgia, serif` — font-weight: 600-700
- Body: `'Inter', sans-serif` — font-weight: 400-600
- Code: `'SF Mono', 'Fira Code', monospace`
- Import: `https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap`

### Components

**Header (lesson-header)**
- badge: uppercase, accent bg, border-radius: 100px
- title: Playfair Display, 2rem, font-weight 700
- subtitle: Inter, 1rem, muted color

**Table of Contents (toc)**
- card-bg background, border, border-radius: 1rem
- Numbering: accent color, font-weight 600

**Sections (section)**
- Heading: Playfair, 1.5rem, number in accent, border-bottom divider
- Body: Inter, 0.9375rem, line-height 1.7

**Cards (card)**
- card-bg, card-border, border-radius: 1rem, padding: 1.25rem
- card-title: font-weight 600

**Code (pre > code)**
- code-bg, card-border, border-radius: 0.75rem
- **REQUIRED:** white-space: pre-wrap; word-wrap: break-word; word-break: break-all
- font-size: 0.8125rem, line-height: 1.6
- color: #e4e4e7

**Tables (table)**
- th: accent color, uppercase, letter-spacing 0.05em
- td: muted color, first td — white font-weight 500
- border-bottom: divider

**Analogy (analogy)**
- accent-dim bg, border-left: 3px solid accent
- label: accent, uppercase, 0.75rem

**Key point (key-point)**
- card-bg, border: accent, border-radius: 1rem
- label: accent, uppercase, bold

**Error box (error-box)**
- bg: rgba(239,68,68,0.1), border: rgba(239,68,68,0.2)
- title: #ef4444

**Summary card (summary-card)**
- accent-dim bg, accent border
- Playfair heading

### Responsive
```css
@media (max-width: 480px) {
  .container { padding: 1rem 1rem 3rem; }
  .lesson-title { font-size: 1.5rem; }
  .section-title { font-size: 1.25rem; }
  pre { padding: 0.75rem; }
}
```

### HTML scaffold
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{title}</title>
<!-- Fonts, CSS vars, styles -->
</head>
<body>
<div class="container">
  <div class="lesson-header">
    <div class="lesson-badge">{badge}</div>
    <h1 class="lesson-title">{title}</h1>
    <p class="lesson-subtitle">{subtitle}</p>
  </div>
  <div class="toc">...</div>
  <!-- sections -->
</div>
</body>
</html>
```

## Content types and structure

### Lesson
- Header with badge "Lesson · {topic}"
- TOC with numbering
- Sections with numbers, code blocks, tables
- Practice at the end, summary table

### Report
- Badge "Report · {date}"
- Key metrics in cards (grid)
- Data tables
- Conclusions in summary-card

### Comparison
- Badge "Comparison"
- Comparison table (th: parameter, columns: options)
- Pros/cons in cards
- Verdict in summary-card

### Roadmap / Plan
- Badge "Roadmap" or "Plan"
- Stages as numbered sections
- Timeline visualization (CSS)
- Statuses: done (green), progress (accent), planned (muted)

### Data / Dashboard
- Badge "Dashboard · {topic}"
- Metrics in grid cards
- Data tables
- Trends described or via ASCII charts

## Rules

- Standalone HTML: single file, no external dependencies except Google Fonts (CDN optional)
- Always dark theme by default
- Responsive: mobile-first, max-width: 100%
- pre/code blocks: ALWAYS white-space:pre-wrap + word-wrap:break-word + word-break:break-all
- Template reference: `assets/template-lesson.html`
