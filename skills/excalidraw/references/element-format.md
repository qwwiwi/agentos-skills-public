# Excalidraw Element Format Reference

## Required Fields (all elements)
`type`, `id` (unique string), `x`, `y`, `width`, `height`

## Defaults (can skip)
strokeColor="#1e1e1e", backgroundColor="transparent", fillStyle="solid", strokeWidth=2, roughness=1, opacity=100

## Element Types

### Rectangle
```json
{"type":"rectangle","id":"r1","x":100,"y":100,"width":200,"height":100}
```
- `roundness: {"type": 3}` for rounded corners
- `backgroundColor: "#a5d8ff"`, `fillStyle: "solid"` for filled

### Ellipse
```json
{"type":"ellipse","id":"e1","x":100,"y":100,"width":150,"height":150}
```

### Diamond
```json
{"type":"diamond","id":"d1","x":100,"y":100,"width":150,"height":150}
```

### Labeled Shape (PREFERRED -- saves tokens)
Add `label` to any shape for auto-centered text:
```json
{"type":"rectangle","id":"r1","x":100,"y":100,"width":200,"height":80,"label":{"text":"Hello","fontSize":20}}
```
Works on rectangle, ellipse, diamond. Text auto-centers, container auto-resizes.

### Standalone Text (titles, annotations only)
```json
{"type":"text","id":"t1","x":150,"y":138,"text":"Hello","fontSize":20}
```
- x is LEFT edge. To center at cx: `x = cx - text.length * fontSize * 0.5 / 2`

### Arrow
```json
{"type":"arrow","id":"a1","x":300,"y":150,"width":200,"height":0,"points":[[0,0],[200,0]],"endArrowhead":"arrow"}
```
- points: [dx, dy] offsets from element x,y
- endArrowhead: null | "arrow" | "bar" | "dot" | "triangle"
- Labeled arrow: `"label": {"text": "connects"}`

### Arrow Bindings
```json
"startBinding": {"elementId":"r1","fixedPoint":[1, 0.5]},
"endBinding": {"elementId":"r2","fixedPoint":[0, 0.5]}
```
fixedPoint: top=[0.5,0], bottom=[0.5,1], left=[0,0.5], right=[1,0.5]

## Camera Control (cameraUpdate pseudo-element)
```json
{"type":"cameraUpdate","width":800,"height":600,"x":0,"y":0}
```
- x, y: top-left corner of visible area
- width, height: MUST be 4:3 ratio
- Sizes: S=400x300, M=600x450, L=800x600 (default), XL=1200x900, XXL=1600x1200
- Always start with cameraUpdate as FIRST element

## Delete (pseudo-element)
```json
{"type":"delete","ids":"b2,a1,t3"}
```
Removes elements by id. Never reuse deleted ids.

## Drawing Order (CRITICAL)
Array order = z-order (first = back, last = front)
Progressive: background → shape → label → arrows → next shape
BAD: all rectangles → all texts → all arrows
GOOD: bg → shape1+label1 → arrow1 → shape2+label2 → ...

## Sizing Rules
- Min fontSize: 16 (body), 20 (titles), 14 (secondary annotations only)
- NEVER fontSize below 14
- Min shape size: 120x60 for labeled rectangles
- Leave 20-30px gaps between elements
- Fewer larger elements > many tiny ones
- Camera padding: 500px content in 800x600 camera

## Text Contrast
- Never light gray (#b0b0b0, #999) on white backgrounds
- Min text color on white: #757575
- For colored text on light fills: use dark variants (#15803d not #22c55e)
- White text needs dark backgrounds

## No Emoji
Excalidraw font doesn't render emoji. Use text labels only.
