"""Generate docs/apple-touch-icon.png — warm steaming-bowl home-screen icon.

Drawn at 4x (720px) with Pillow, downscaled to 180x180 for anti-aliasing.
Run: python tools/make_icon.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 720  # 4x supersample, final 180
OUT = Path(__file__).resolve().parent.parent / "docs" / "apple-touch-icon.png"

TOP = (247, 166, 41)     # warm amber
BOTTOM = (219, 84, 18)   # deep orange
CREAM = (255, 247, 234)
BAND = (232, 138, 45)    # decorative stripe on the bowl
SHADOW = (120, 40, 5, 70)
STEAM = (255, 255, 255, 235)


def lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


img = Image.new("RGB", (SIZE, SIZE))
for y in range(SIZE):
    img.paste(lerp(TOP, BOTTOM, y / (SIZE - 1)), (0, y, SIZE, y + 1))

draw = ImageDraw.Draw(img, "RGBA")

cx, rim_y, r = 360, 400, 215

# ground shadow
draw.ellipse((cx - r + 30, 600, cx + r - 30, 665), fill=SHADOW)

# bowl: bottom half-disc + foot
draw.pieslice((cx - r, rim_y - r, cx + r, rim_y + r), 0, 180, fill=CREAM)
draw.rounded_rectangle((cx - 70, rim_y + 195, cx + 70, rim_y + 235), radius=18, fill=CREAM)

# decorative band just under the rim (clipped to the bowl silhouette)
band = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
ImageDraw.Draw(band).rectangle((cx - r, rim_y + 55, cx + r, rim_y + 95), fill=BAND + (255,))
mask = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(mask).pieslice((cx - r, rim_y - r, cx + r, rim_y + r), 0, 180, fill=255)
img.paste(band, (0, 0), Image.composite(band.split()[3], Image.new("L", (SIZE, SIZE), 0), mask))

# rim: slight top ellipse for a hint of depth
draw.ellipse((cx - r, rim_y - 16, cx + r, rim_y + 16), fill=CREAM)

# steam: three wavy curls with rounded ends
for sx, top, phase in ((250, 190, 0.0), (360, 130, math.pi), (470, 190, 0.0)):
    pts = []
    for i in range(41):
        t = i / 40
        y = 350 - t * (350 - top)
        x = sx + math.sin(t * 2 * math.pi + phase) * 26
        pts.append((x, y))
    draw.line(pts, fill=STEAM, width=30, joint="curve")
    for x, y in (pts[0], pts[-1]):
        draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=STEAM)

img.resize((180, 180), Image.LANCZOS).save(OUT)
print(f"wrote {OUT}")
