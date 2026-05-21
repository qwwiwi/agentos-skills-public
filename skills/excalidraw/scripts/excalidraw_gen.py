#!/usr/bin/env python3
"""
Excalidraw diagram generator v2.0
Supports: pipeline, mindmap, flowchart, sequence, freeform
Color palette: MCP Excalidraw standard
"""
import argparse
import json
import math
import random
import sys
import time
from typing import Dict, List, Tuple, Optional

# === MCP Standard Color Palette ===
COLORS = {
    # Semantic types
    "input":     {"background": "#ffc9c9", "stroke": "#ef4444"},
    "research":  {"background": "#a5d8ff", "stroke": "#4a9eed"},
    "analysis":  {"background": "#d0bfff", "stroke": "#8b5cf6"},
    "review":    {"background": "#ffd8a8", "stroke": "#f59e0b"},
    "final":     {"background": "#b2f2bb", "stroke": "#22c55e"},
    "factcheck": {"background": "#b2f2bb", "stroke": "#22c55e"},
    "storage":   {"background": "#c3fae8", "stroke": "#06b6d4"},
    "data":      {"background": "#c3fae8", "stroke": "#06b6d4"},
    "warning":   {"background": "#fff3bf", "stroke": "#f59e0b"},
    "error":     {"background": "#ffc9c9", "stroke": "#ef4444"},
    "info":      {"background": "#a5d8ff", "stroke": "#06b6d4"},
    "success":   {"background": "#b2f2bb", "stroke": "#22c55e"},
    "metrics":   {"background": "#eebefa", "stroke": "#ec4899"},
    "default":   {"background": "#f8f9fa", "stroke": "#495057"},
}

# Zone backgrounds (opacity 30-35)
ZONES = {
    "frontend": {"background": "#dbe4ff", "stroke": "#4a9eed"},
    "backend":  {"background": "#e5dbff", "stroke": "#8b5cf6"},
    "data":     {"background": "#d3f9d8", "stroke": "#22c55e"},
}

# Dark mode
DARK_COLORS = {
    "input":     {"background": "#5c1a1a", "stroke": "#ef4444"},
    "research":  {"background": "#1e3a5f", "stroke": "#4a9eed"},
    "analysis":  {"background": "#2d1b69", "stroke": "#8b5cf6"},
    "review":    {"background": "#5c3d1a", "stroke": "#f59e0b"},
    "final":     {"background": "#1a4d2e", "stroke": "#22c55e"},
    "factcheck": {"background": "#1a4d2e", "stroke": "#22c55e"},
    "storage":   {"background": "#1a4d4d", "stroke": "#06b6d4"},
    "data":      {"background": "#1a4d4d", "stroke": "#06b6d4"},
    "default":   {"background": "#2a2a3a", "stroke": "#a0a0a0"},
}

ARROW_COLOR = "#495057"
ARROW_COLOR_DARK = "#a0a0a0"
BG_COLOR = "#ffffff"
BG_COLOR_DARK = "#1e1e2e"
TEXT_COLOR = "#1e1e1e"
TEXT_COLOR_DARK = "#e5e5e5"
TEXT_SECONDARY_DARK = "#a0a0a0"

FONT_BLOCK = 18
FONT_STAGE = 20
FONT_TITLE = 28
FONT_FAMILY = 1
STROKE_WIDTH = 2
ROUGHNESS = 0

# Camera sizes (4:3 ratio)
CAMERA = {
    "S":   (400, 300),
    "M":   (600, 450),
    "L":   (800, 600),
    "XL":  (1200, 900),
    "XXL": (1600, 1200),
}


def rand_seed() -> int:
    return random.randint(1, 2_000_000_000)


def ex_id(prefix="el"):
    return f"{prefix}_{int(time.time()*1000)}_{random.randint(1000,9999)}"


def text_size(text: str, base_w=220, line_h=26, pad=24, font_size=18) -> Tuple[int, int]:
    lines = (text or "").split("\n")
    max_len = max((len(l) for l in lines), default=8)
    char_w = font_size * 0.6
    width = max(base_w, min(600, int(max_len * char_w + pad * 2)))
    height = max(64, int(len(lines) * (font_size * 1.4) + pad))
    return width, height


def mk_camera(x=0, y=0, size="L") -> Dict:
    w, h = CAMERA.get(size, CAMERA["L"])
    return {"type": "cameraUpdate", "width": w, "height": h, "x": x, "y": y}


def mk_dark_bg() -> Dict:
    return {
        "id": ex_id("darkbg"),
        "type": "rectangle",
        "x": -4000, "y": -3000, "width": 10000, "height": 7500,
        "backgroundColor": BG_COLOR_DARK, "fillStyle": "solid",
        "strokeColor": "transparent", "strokeWidth": 0,
        "angle": 0, "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": rand_seed(), "version": 1, "versionNonce": rand_seed(),
        "isDeleted": False, "boundElements": [], "updated": int(time.time()*1000),
        "link": None, "locked": False,
    }


def mk_rect(x, y, w, h, color, label=None, dark=False):
    el = {
        "id": ex_id("rect"),
        "type": "rectangle",
        "x": x, "y": y, "width": w, "height": h,
        "angle": 0,
        "strokeColor": color["stroke"],
        "backgroundColor": color["background"],
        "fillStyle": "solid",
        "strokeWidth": STROKE_WIDTH,
        "strokeStyle": "solid",
        "roughness": ROUGHNESS,
        "opacity": 100,
        "groupIds": [], "frameId": None,
        "roundness": {"type": 3},
        "seed": rand_seed(), "version": 1, "versionNonce": rand_seed(),
        "isDeleted": False, "boundElements": [],
        "updated": int(time.time()*1000),
        "link": None, "locked": False,
    }
    if label:
        el["label"] = {
            "text": label.get("text", ""),
            "fontSize": label.get("fontSize", FONT_BLOCK),
        }
        if dark:
            el["label"]["strokeColor"] = TEXT_COLOR_DARK
    return el


def mk_text(x, y, text, font_size, color=None, w=None, h=None, dark=False):
    if color is None:
        color = TEXT_COLOR_DARK if dark else TEXT_COLOR
    if w is None or h is None:
        w, h = text_size(text, base_w=120, font_size=font_size)
    return {
        "id": ex_id("txt"),
        "type": "text",
        "x": x, "y": y, "width": w, "height": h,
        "angle": 0,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "hachure",
        "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": rand_seed(), "version": 1, "versionNonce": rand_seed(),
        "isDeleted": False, "boundElements": [],
        "updated": int(time.time()*1000),
        "link": None, "locked": False,
        "text": text, "fontSize": font_size, "fontFamily": FONT_FAMILY,
        "textAlign": "center", "verticalAlign": "middle",
        "containerId": None, "originalText": text, "lineHeight": 1.25,
    }


def mk_arrow(x1, y1, x2, y2, label=None, dark=False, dashed=False, arrowhead="arrow"):
    el = {
        "id": ex_id("arr"),
        "type": "arrow",
        "x": x1, "y": y1,
        "width": x2 - x1, "height": y2 - y1,
        "angle": 0,
        "strokeColor": ARROW_COLOR_DARK if dark else ARROW_COLOR,
        "backgroundColor": "transparent",
        "fillStyle": "hachure",
        "strokeWidth": STROKE_WIDTH,
        "strokeStyle": "dashed" if dashed else "solid",
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": rand_seed(), "version": 1, "versionNonce": rand_seed(),
        "isDeleted": False, "boundElements": [],
        "updated": int(time.time()*1000),
        "link": None, "locked": False,
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
        "startBinding": None, "endBinding": None,
        "startArrowhead": None, "endArrowhead": arrowhead,
    }
    if label:
        el["label"] = {"text": label, "fontSize": 14}
    return el


def color_of(name: str, dark=False):
    palette = DARK_COLORS if dark else COLORS
    return palette.get((name or "").lower(), palette.get("default", COLORS["default"]))


def build_pipeline(schema: Dict) -> List[Dict]:
    dark = schema.get("dark", False)
    els = []
    title = schema.get("title", "Pipeline")
    stages = schema.get("stages", [])

    # Camera
    total_h = len(stages) * 230 + 100
    cam_size = "L" if total_h < 600 else "XL" if total_h < 900 else "XXL"
    cam_w, cam_h = CAMERA[cam_size]
    els.append(mk_camera(x=-cam_w//2 + 50, y=-280, size=cam_size))

    if dark:
        els.insert(0, mk_dark_bg())

    title_w, title_h = text_size(title, base_w=400, line_h=38, pad=20, font_size=FONT_TITLE)
    els.append(mk_text(-title_w // 2, -260, title, FONT_TITLE, w=title_w, h=title_h, dark=dark))

    y = -120
    stage_gap = 190
    prev_center = None

    for s in stages:
        label = s.get("label", "Stage")
        subtitle = s.get("subtitle")
        blocks = s.get("blocks", [])
        stage_color = color_of(s.get("color", "default"), dark)

        label_w, label_h = text_size(label, base_w=360, line_h=30, pad=24, font_size=FONT_STAGE)
        label_rect = mk_rect(-label_w // 2, y, label_w, 70, stage_color, label={"text": label, "fontSize": FONT_STAGE}, dark=dark)
        els.append(label_rect)

        if subtitle:
            sub_w, sub_h = text_size(subtitle, base_w=220, line_h=24, pad=10, font_size=16)
            sub_color = TEXT_SECONDARY_DARK if dark else "#6b7280"
            els.append(mk_text(-sub_w // 2, y + 78, subtitle, 16, color=sub_color, w=sub_w, h=sub_h))

        block_y = y + 95
        n = max(1, len(blocks))
        gap = 40
        widths = []
        for b in blocks:
            w, _ = text_size(b.get("text", ""), base_w=220, font_size=FONT_BLOCK)
            widths.append(w)
        total_w = sum(widths) + gap * (n - 1)
        start_x = -total_w // 2

        for i, b in enumerate(blocks):
            btxt = b.get("text", "")
            bw, bh = text_size(btxt, font_size=FONT_BLOCK)
            bx = start_x + sum(widths[:i]) + i * gap
            bcolor = color_of(b.get("color", s.get("color", "default")), dark)
            rect = mk_rect(bx, block_y, bw, bh, bcolor, label={"text": btxt, "fontSize": FONT_BLOCK}, dark=dark)
            els.append(rect)
            els.append(mk_arrow(0, y + 70, bx + bw // 2, block_y, dark=dark))

        stage_center = (0, y + 35)
        if prev_center:
            els.append(mk_arrow(prev_center[0], prev_center[1] + 90, stage_center[0], stage_center[1], dark=dark))
        prev_center = stage_center
        y += stage_gap + 40

    return els


def build_mindmap(schema: Dict) -> List[Dict]:
    dark = schema.get("dark", False)
    els = []
    title = schema.get("title", "Mind Map")
    nodes = schema.get("nodes", [])

    els.append(mk_camera(size="L"))
    if dark:
        els.insert(0, mk_dark_bg())

    cw, ch = text_size(title, base_w=280, font_size=FONT_STAGE)
    c_rect = mk_rect(-cw // 2, -ch // 2, cw, ch, color_of("analysis", dark),
                      label={"text": title, "fontSize": FONT_STAGE}, dark=dark)
    els.append(c_rect)

    radius = 320
    for i, n in enumerate(nodes):
        angle = (2 * math.pi * i) / max(1, len(nodes))
        nx = int(math.cos(angle) * radius)
        ny = int(math.sin(angle) * radius)
        txt = n.get("text", n.get("label", "Node"))
        col = color_of(n.get("color", "research"), dark)
        w, h = text_size(txt, base_w=180, font_size=FONT_BLOCK)
        r = mk_rect(nx - w // 2, ny - h // 2, w, h, col,
                     label={"text": txt, "fontSize": FONT_BLOCK}, dark=dark)
        els.extend([r, mk_arrow(0, 0, nx, ny, dark=dark)])

    return els


def build_flowchart(schema: Dict) -> List[Dict]:
    dark = schema.get("dark", False)
    els = []
    nodes = schema.get("nodes", [])
    edges = schema.get("edges", [])
    title = schema.get("title")

    els.append(mk_camera(size="L"))
    if dark:
        els.insert(0, mk_dark_bg())

    if title:
        tw, th = text_size(title, base_w=420, line_h=38, font_size=FONT_TITLE)
        els.append(mk_text(-tw // 2, -280, title, FONT_TITLE, w=tw, h=th, dark=dark))

    id_to_center = {}
    for n in nodes:
        nid = n.get("id", ex_id("n"))
        x = int(n.get("x", 0))
        y = int(n.get("y", 0))
        txt = n.get("text", n.get("label", nid))
        col = color_of(n.get("color", "default"), dark)
        w, h = text_size(txt, font_size=FONT_BLOCK)
        r = mk_rect(x, y, w, h, col, label={"text": txt, "fontSize": FONT_BLOCK}, dark=dark)
        els.append(r)
        id_to_center[nid] = (x + w // 2, y + h // 2)

    for e in edges:
        s = id_to_center.get(e.get("from"))
        t = id_to_center.get(e.get("to"))
        if s and t:
            lbl = e.get("label")
            els.append(mk_arrow(s[0], s[1], t[0], t[1], label=lbl, dark=dark))

    return els


def build_sequence(schema: Dict) -> List[Dict]:
    """Build UML-style sequence diagram."""
    dark = schema.get("dark", False)
    els = []
    title = schema.get("title", "Sequence")
    actors = schema.get("actors", [])
    messages = schema.get("messages", [])

    n_actors = len(actors)
    actor_gap = 200
    total_w = actor_gap * max(1, n_actors - 1) + 200
    start_x = -total_w // 2

    els.append(mk_camera(x=start_x - 50, y=-30, size="XL" if n_actors > 4 else "L"))
    if dark:
        els.insert(0, mk_dark_bg())

    # Title
    if title:
        tw, th = text_size(title, base_w=400, font_size=24)
        els.append(mk_text(start_x, 0, title, 24, w=tw, h=th, dark=dark))

    # Actor headers + lifelines
    actor_x = {}
    lifeline_h = len(messages) * 50 + 150
    actor_colors = ["#a5d8ff", "#d0bfff", "#b2f2bb", "#ffd8a8", "#ffc9c9", "#c3fae8", "#fff3bf", "#eebefa"]
    actor_strokes = ["#4a9eed", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#f59e0b", "#ec4899"]

    for i, a in enumerate(actors):
        ax = start_x + i * actor_gap
        actor_x[a.get("id", a.get("name", f"a{i}"))] = ax + 65
        col = {"background": actor_colors[i % len(actor_colors)], "stroke": actor_strokes[i % len(actor_strokes)]}
        name = a.get("name", a.get("id", f"Actor {i+1}"))
        rect = mk_rect(ax, 50, 130, 40, col, label={"text": name, "fontSize": 16}, dark=dark)
        els.append(rect)
        els.append(mk_arrow(ax + 65, 90, ax + 65, 90 + lifeline_h, dark=dark, dashed=True, arrowhead=None))

    # Messages
    msg_y = 120
    for m in messages:
        from_x = actor_x.get(m.get("from"), 0)
        to_x = actor_x.get(m.get("to"), 200)
        lbl = m.get("label", "")
        is_response = m.get("response", False)
        els.append(mk_arrow(from_x, msg_y, to_x, msg_y, label=lbl, dark=dark, dashed=is_response))
        msg_y += 50

    return els


def build_freeform(schema: Dict) -> List[Dict]:
    """Pass raw Excalidraw elements through."""
    return schema.get("elements", [])


def build(schema: Dict) -> Dict:
    kind = (schema.get("type") or "pipeline").lower()
    dark = schema.get("dark", False)

    builders = {
        "pipeline": build_pipeline,
        "mindmap": build_mindmap, "mind_map": build_mindmap, "mind-map": build_mindmap,
        "flowchart": build_flowchart,
        "sequence": build_sequence,
        "freeform": build_freeform, "raw": build_freeform,
    }

    builder = builders.get(kind)
    if not builder:
        raise ValueError(f"Unsupported type: {kind}. Supported: {', '.join(builders.keys())}")

    elements = builder(schema)

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://openclaw.local/skills/excalidraw",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": BG_COLOR_DARK if dark else BG_COLOR,
        },
        "files": {},
    }


def load_input(path: str = None) -> Dict:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input JSON provided via stdin or --input")
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description="Generate Excalidraw diagrams from JSON schema (v2.0)")
    parser.add_argument("--input", "-i", help="Input schema JSON file")
    parser.add_argument("--output", "-o", help="Output .excalidraw file")
    parser.add_argument("--dark", action="store_true", help="Dark mode")
    args = parser.parse_args()

    schema = load_input(args.input)
    if args.dark:
        schema["dark"] = True
    doc = build(schema)
    out = json.dumps(doc, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
            f.write("\n")
    else:
        print(out)


if __name__ == "__main__":
    main()
