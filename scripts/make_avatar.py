#!/usr/bin/env python3
"""Crop a centered selfie to a circular gold-ringed avatar for the Remotion HUD.

No face-detection dependency: assumes a roughly centered portrait and frames
head+shoulders with generous headroom (safe for small HUD display).
Usage: python3 scripts/make_avatar.py <src.jpg> [out.png] [size]
"""
import sys
from PIL import Image
import numpy as np

SRC = sys.argv[1] if len(sys.argv) > 1 else None
OUT = sys.argv[2] if len(sys.argv) > 2 else "public/avatar.png"
SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 256
GOLD = (232, 176, 75)

assert SRC, "need source path"
img = Image.open(SRC).convert("RGB")
w, h = img.size
print(f"src {w}x{h}")

# Optional explicit crop: <cx> <cy> <side> in source pixels (args 4,5,6).
if len(sys.argv) > 6:
    cx, cy, side = int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
    print(f"crop cx={cx} cy={cy} side={side} (explicit)")
else:
    # Head-centered square tuned on a 1208x1744 selfie (head top ~26%, chin ~80%,
    # face center x ~51%). Gives even margins so the disc never clips the head.
    cx = w // 2
    cy = int(h * 0.53)
    side = int(min(w, h) * 0.96)
half = side // 2
x0 = max(0, cx - half); y0 = max(0, cy - half)
x1 = min(w, cx + side - half); y1 = min(h, cy + side - half)
crop = img.crop((x0, y0, x1, y1))
ch, cw = crop.size
if ch != cw:
    s = max(ch, cw)
    pad = Image.new("RGB", (s, s), (0, 0, 0))
    pad.paste(crop, ((s - cw) // 2, (s - ch) // 2))
    crop = pad

work = 512
base = crop.resize((work, work), Image.LANCZOS)

# circular alpha with feather at the rim
R = work // 2
yy, xx = np.ogrid[:work, :work]
dist = np.sqrt((xx - R) ** 2 + (yy - R) ** 2)
feather = 6
alpha = np.zeros((work, work), dtype=np.uint8)
alpha[(dist <= R - feather)] = 255
band = (dist > R - feather) & (dist < R)
alpha[band] = np.clip(255 - (dist[band] - (R - feather)) / feather * 255, 0, 255).astype(np.uint8)

# vignette so busy background fades into the dark HUD
vig = np.clip(1.0 - (dist / R) ** 2 * 0.35, 0, 1)
arr = np.array(base, dtype=np.float32)
for c in range(3):
    arr[..., c] *= vig
base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

out = Image.new("RGBA", (work, work), (0, 0, 0, 0))
out.paste(base, (0, 0))
out.putalpha(Image.fromarray(alpha, "L"))

# gold ring just inside the rim (anti-aliased), masked to face alpha
ringd = np.zeros((work, work), dtype=np.uint8)
rw = 5
ringd[(dist >= R - rw - feather) & (dist <= R - feather)] = 255
ring = Image.new("RGBA", (work, work), GOLD + (0,))
ring.putalpha(Image.fromarray(ringd, "L"))
fa = alpha.astype(np.int32)
ra = np.clip(np.array(ring.split()[-1], dtype=np.int32) * (fa / 255.0), 0, 255).astype(np.uint8)
ring.putalpha(Image.fromarray(ra, "L"))
out = Image.alpha_composite(out, ring)

out = out.resize((SIZE, SIZE), Image.LANCZOS)
out.save(OUT)
print(f"saved {OUT} {out.size}")
