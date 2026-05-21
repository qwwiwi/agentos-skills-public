# Excalidraw Examples

## Example 1: Two Connected Labeled Boxes
```json
[
  {"type":"cameraUpdate","width":800,"height":600,"x":50,"y":50},
  {"type":"rectangle","id":"b1","x":100,"y":100,"width":200,"height":100,"roundness":{"type":3},"backgroundColor":"#a5d8ff","fillStyle":"solid","label":{"text":"Start","fontSize":20}},
  {"type":"rectangle","id":"b2","x":450,"y":100,"width":200,"height":100,"roundness":{"type":3},"backgroundColor":"#b2f2bb","fillStyle":"solid","label":{"text":"End","fontSize":20}},
  {"type":"arrow","id":"a1","x":300,"y":150,"width":150,"height":0,"points":[[0,0],[150,0]],"endArrowhead":"arrow","startBinding":{"elementId":"b1","fixedPoint":[1,0.5]},"endBinding":{"elementId":"b2","fixedPoint":[0,0.5]}}
]
```

## Example 2: Architecture with Zones
```json
[
  {"type":"cameraUpdate","width":800,"height":600,"x":-20,"y":-20},
  {"type":"rectangle","id":"zone1","x":0,"y":0,"width":350,"height":500,"backgroundColor":"#dbe4ff","fillStyle":"solid","roundness":{"type":3},"strokeColor":"#4a9eed","strokeWidth":1,"opacity":35},
  {"type":"text","id":"z1l","x":10,"y":6,"text":"Frontend Layer","fontSize":16,"strokeColor":"#2563eb"},
  {"type":"rectangle","id":"zone2","x":400,"y":0,"width":350,"height":500,"backgroundColor":"#e5dbff","fillStyle":"solid","roundness":{"type":3},"strokeColor":"#8b5cf6","strokeWidth":1,"opacity":35},
  {"type":"text","id":"z2l","x":410,"y":6,"text":"Backend Layer","fontSize":16,"strokeColor":"#6b21a8"},
  {"type":"rectangle","id":"ui","x":40,"y":60,"width":180,"height":70,"roundness":{"type":3},"backgroundColor":"#a5d8ff","fillStyle":"solid","label":{"text":"React App","fontSize":18}},
  {"type":"rectangle","id":"api","x":440,"y":60,"width":180,"height":70,"roundness":{"type":3},"backgroundColor":"#d0bfff","fillStyle":"solid","label":{"text":"API Server","fontSize":18}},
  {"type":"arrow","id":"a1","x":220,"y":95,"width":220,"height":0,"points":[[0,0],[220,0]],"endArrowhead":"arrow","label":{"text":"REST/gRPC","fontSize":14}},
  {"type":"rectangle","id":"db","x":440,"y":200,"width":180,"height":70,"roundness":{"type":3},"backgroundColor":"#c3fae8","fillStyle":"solid","label":{"text":"PostgreSQL","fontSize":18}},
  {"type":"arrow","id":"a2","x":530,"y":130,"width":0,"height":70,"points":[[0,0],[0,70]],"endArrowhead":"arrow"}
]
```

## Example 3: Sequence Diagram Pattern
Use dashed lifelines + horizontal arrows for sequence flows:
- Actor headers: colored rectangles at top
- Lifelines: `"strokeStyle":"dashed"` arrows going down
- Messages: horizontal arrows between lifelines with labels

## Example 4: Dark Mode
Start with dark background, use dark fills and light text:
```json
[
  {"type":"rectangle","id":"darkbg","x":-4000,"y":-3000,"width":10000,"height":7500,"backgroundColor":"#1e1e2e","fillStyle":"solid","strokeColor":"transparent","strokeWidth":0},
  {"type":"cameraUpdate","width":800,"height":600,"x":0,"y":0},
  {"type":"rectangle","id":"b1","x":100,"y":100,"width":200,"height":80,"roundness":{"type":3},"backgroundColor":"#1e3a5f","fillStyle":"solid","strokeColor":"#4a9eed","label":{"text":"Node","fontSize":20,"strokeColor":"#e5e5e5"}}
]
```

## Tips
- cameraUpdate is MAGICAL -- use it to guide attention
- Progressive drawing: draw section by section with camera moves
- Arrow labels need space -- keep short or make arrows wider
- Leave padding between camera edges and content
- Draw art/illustrations LAST
