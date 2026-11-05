# Brand references registry

`brands.json` maps preset names to reference images (paths on your machine, images are NOT
copied here) and style notes. It is your private file: it is in `.gitignore` and is not part of
the repo. Start from the example:

```bash
cp references/brands.example.json references/brands.json
# then replace every path with your own files
python3 scripts/brief.py presets
```

A brief pulls a preset with `"preset": "<name>"`; preset refs come first, then the brief's own
refs. Drop preset refs by role with `"preset_replace_roles": ["logo"]` (e.g. a cover about
another brand).

| Example preset | Refs | Use for |
|---|---|---|
| `my-face` | 2 face | any image with the author's face |
| `youtube-dark` | 2 face + 2 reference covers + product logo | YouTube covers |
| `my-brand` | logo + 2 banners | brand posts, banners |

Rules:
- Faces: only approved frames (eyes fully open, direct gaze). Move rejected frames (blink,
  squint, side gaze) into a folder named `_rejected/` – `brief.py check` fails on them.
- Logos must be PNG/JPG/WEBP: the subscription does not accept SVG, rasterize it first.
- Adding a preset: every ref has a role
  (subject|face|style|logo|background|layout|clothing), then run `brief.py presets`.
