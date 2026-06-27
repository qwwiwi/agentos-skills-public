#!/usr/bin/env python3
"""Cut the person out of a photo onto a transparent background (rembg, human seg).

Usage:  python cutout.py in.png out.png
Run with the skill venv that has rembg: <skill>/.venv/bin/python cutout.py ...

Notes:
  - Uses model u2net_human_seg (best for people); downloads to ~/.u2net on first run.
  - Use the Python API, NOT the CLI (CLI needs rembg[cli] extra; the API ships with rembg).
  - Resize tall/vertical source to ~1280px height BEFORE cutout for speed/quality.
"""
from __future__ import annotations

import sys
from rembg import remove, new_session
from PIL import Image


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: cutout.py in.png out.png")
    src, dst = sys.argv[1], sys.argv[2]
    sess = new_session("u2net_human_seg")
    img = Image.open(src)
    # keep height sane for speed (face only needs ~720-1280px in a thumbnail)
    if img.height > 1400:
        img = img.resize((round(img.width * 1280 / img.height), 1280))
    out = remove(img, session=sess, post_process_mask=True)
    out.save(dst)
    print(f"{dst} {out.size}")


if __name__ == "__main__":
    main()
