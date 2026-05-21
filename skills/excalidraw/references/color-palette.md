# Excalidraw Color Palette (MCP Standard)

## Primary Colors (stroke, text accents, arrows)
| Name | Hex | Use |
|------|-----|-----|
| Blue | `#4a9eed` | Primary actions, links, data series 1 |
| Amber | `#f59e0b` | Warnings, highlights, data series 2 |
| Green | `#22c55e` | Success, positive, data series 3 |
| Red | `#ef4444` | Errors, negative, data series 4 |
| Purple | `#8b5cf6` | Accents, special items, data series 5 |
| Pink | `#ec4899` | Decorative, data series 6 |
| Cyan | `#06b6d4` | Info, secondary, data series 7 |
| Lime | `#84cc16` | Extra, data series 8 |

## Shape Fills (pastel, for backgrounds)
| Color | Hex | Good For |
|-------|-----|----------|
| Light Blue | `#a5d8ff` | Input, sources, primary nodes |
| Light Green | `#b2f2bb` | Success, output, completed |
| Light Orange | `#ffd8a8` | Warning, pending, external |
| Light Purple | `#d0bfff` | Processing, middleware, special |
| Light Red | `#ffc9c9` | Error, critical, alerts |
| Light Yellow | `#fff3bf` | Notes, decisions, planning |
| Light Teal | `#c3fae8` | Storage, data, memory |
| Light Pink | `#eebefa` | Analytics, metrics |

## Background Zones (opacity: 30-35 for layered diagrams)
| Color | Hex | Good For |
|-------|-----|----------|
| Blue zone | `#dbe4ff` | UI / frontend layer |
| Purple zone | `#e5dbff` | Logic / agent layer |
| Green zone | `#d3f9d8` | Data / tool layer |

## Semantic Mapping (skill types)
| Type | Fill | Stroke |
|------|------|--------|
| input | `#ffc9c9` | `#ef4444` |
| research | `#a5d8ff` | `#4a9eed` |
| analysis | `#d0bfff` | `#8b5cf6` |
| review | `#ffd8a8` | `#f59e0b` |
| final / factcheck | `#b2f2bb` | `#22c55e` |
| storage / data | `#c3fae8` | `#06b6d4` |
| warning | `#fff3bf` | `#f59e0b` |
| default | `#f8f9fa` | `#495057` |

## Dark Mode Colors
### Shape fills
| Color | Hex | Good For |
|-------|-----|----------|
| Dark Blue | `#1e3a5f` | Primary nodes |
| Dark Green | `#1a4d2e` | Success, output |
| Dark Purple | `#2d1b69` | Processing, special |
| Dark Orange | `#5c3d1a` | Warning, pending |
| Dark Red | `#5c1a1a` | Error, critical |
| Dark Teal | `#1a4d4d` | Storage, data |

### Text on dark
| Color | Hex | Use |
|-------|-----|-----|
| White | `#e5e5e5` | Primary text, titles |
| Muted | `#a0a0a0` | Secondary text, annotations |
| NEVER | `#555` or darker | Invisible on dark bg |

### Dark background element
```json
{"type":"rectangle","id":"darkbg","x":-4000,"y":-3000,"width":10000,"height":7500,"backgroundColor":"#1e1e2e","fillStyle":"solid","strokeColor":"transparent","strokeWidth":0}
```
Place as FIRST element before cameraUpdate.
