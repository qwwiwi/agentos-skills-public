---
name: datawrapper
description: Create Datawrapper charts/tables from CSV, JSON, or inline data; publish and export PNG. Use when user wants a chart, embeddable visualization, or PNG for Telegram.
---

# Datawrapper Chart Skill

## What it does
Creates charts and tables via Datawrapper API (datawrapper.de). Accepts CSV, JSON, or inline data. Publishes and optionally exports PNG.

## When to use
- User asks for a chart, graph, or table from data
- Result should be embeddable or shareable via URL
- Need PNG to send in chat/Telegram
- Triggers: "chart", "graph", "dashboard", "visualization", "datawrapper", "embed"

## Do NOT use when
- Only need a local matplotlib image (no hosting)
- Need PDF/SVG export (paid Datawrapper plan)
- Browser automation required

## Requirements
Environment variable: `DATAWRAPPER_API_KEY`
Token scopes: `chart:write`, `chart:read`, `theme:read`, `visualization:read`

Get your API key at: https://app.datawrapper.de/account/api-tokens

## Chart types

| Visual | Type ID |
|--------|---------|
| Bar (horizontal) | d3-bars |
| Stacked bar | d3-bars-stacked |
| Column (vertical) | column-chart |
| Line | d3-lines |
| Area | d3-area |
| Pie | d3-pies |
| Scatter | d3-scatter-plot |
| Table | tables |

See `references/chart-types.md` for the full list including maps.

## Command

```bash
python3 {baseDir}/scripts/datawrapper_chart.py \
  --type d3-bars \
  --data-file /path/to/data.csv \
  --title "My Chart" \
  --publish --export-png
```

## All arguments

| Arg | Required | Default | Description |
|-----|----------|---------|-------------|
| --type | yes | -- | Chart type ID |
| --data-file | * | -- | Path to CSV or JSON file |
| --data-inline | * | -- | Inline CSV/JSON string |
| --input-format | no | auto | Force: csv, json, table, auto |
| --title | no | -- | Chart title |
| --publish | no | false | Publish after creation |
| --export-png | no | false | Download PNG (requires --publish) |
| --output-dir | no | /tmp | Directory for PNG |
| --dark | no | false | Dark theme (ID: datawrapper-dark) |
| --theme | no | -- | Custom theme ID (overrides --dark) |
| --folder-id | no | -- | Datawrapper folder ID |
| --byline | no | -- | Author byline |
| --source-name | no | -- | Data source name |
| --source-url | no | -- | Data source URL |
| --notes | no | -- | Chart annotations |
| --width | no | -- | Export width (px) |
| --height | no | -- | Export height (px) |
| --png-zoom | no | 2 | PNG zoom factor |
| --png-plain | no | false | No header/footer |
| --png-transparent | no | false | Transparent background |
| --png-border-width | no | 20 | PNG border width (px) |

*One of --data-file or --data-inline required.

## Input formats
1. **CSV file**: `--data-file prices.csv`
2. **JSON file**: `--data-file buys.json` (array of objects or {columns, rows})
3. **Inline CSV**: `--data-inline "date,price\n2026-03-01,82000"`
4. **Pipe table**: auto-detected, split on `|`

Max file size: 10MB.

## Output
Structured JSON to stdout:
```json
{
  "ok": true,
  "chart_id": "Ab12C",
  "chart_type": "d3-lines",
  "edit_url": "https://app.datawrapper.de/chart/Ab12C/visualize",
  "public_url": "https://datawrapper.dwcdn.net/Ab12C/1/",
  "embed_url": "https://datawrapper.dwcdn.net/Ab12C/1/",
  "png_path": "/tmp/Ab12C.png"
}
```

## Examples

Bar chart from CSV + PNG export:
```bash
python3 {baseDir}/scripts/datawrapper_chart.py \
  --type d3-bars \
  --data-file /tmp/data.csv \
  --title "My Chart" \
  --source-name "Data source" \
  --publish --export-png
```

Line chart inline:
```bash
python3 {baseDir}/scripts/datawrapper_chart.py \
  --type d3-lines \
  --data-inline "date,price
2026-03-01,70000
2026-03-15,74000" \
  --title "Price History" --publish
```

## Notes
- Free plan: unlimited create + publish + PNG export
- Free plan shows "Created with Datawrapper" watermark
- PDF/SVG export requires paid plan
- `--dark` uses theme ID `datawrapper-dark`. If unavailable on your account, use `--theme` with your custom theme ID
- PNG export retries up to 3 times on transient errors
