"""Turns the hand-drawn / painted crystal sword art into the mod's animated sword texture.

Source:  tools/sword_source.png   - your art. Any square frame size works; a multi-frame strip
                                    (frames stacked vertically) is fine too, this script only
                                    keeps the most complete frame as the base drawing.
Output:  assets/lightning_sword/textures/item/lightning_sword.png  - 8 frames, one per FRAMES,
                                    each with its own procedural lightning crawling over the
                                    blade plus a pulsing cyan rim glow, so the blade crackles
                                    in game instead of being a still picture.

Run:  python tools/build_sword_texture.py
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(PROJECT, 'tools', 'sword_source.png')
ASSETS = os.path.join(PROJECT, 'src', 'main', 'resources', 'assets', 'lightning_sword')
OUT = os.path.join(ASSETS, 'textures', 'item', 'lightning_sword.png')

FRAMES = 8
# How much of the drawing's diagonal the lightning is allowed to run along.
ARC_START = 0.18
ARC_END = 0.98
ARC_COUNT = 4

if not os.path.exists(SOURCE):
    raise SystemExit('Missing %s - put your sword art there first.' % SOURCE)

source = Image.open(SOURCE).convert('RGBA')
width, height = source.size
frame_height = width
frame_count = max(1, height // frame_height)
drawings = [source.crop((0, i * frame_height, width, (i + 1) * frame_height))
            for i in range(frame_count)]
print('source: %dx%d, %d frame(s) of %dx%d' % (width, height, frame_count, width, frame_height))


def opaque_pixels(image):
    return sum(1 for pixel in image.getdata() if pixel[3] > 200)


base = max(drawings, key=opaque_pixels)
print('base frame: index %d of %d' % (drawings.index(base), frame_count))

alpha = base.getchannel('A').point(lambda v: 255 if v > 24 else 0)
box = alpha.getbbox()
if box is None:
    raise SystemExit('The source art is fully transparent.')

# The gem: everything just outside the silhouette, blurred, tinted cyan.
ring = ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(11)), alpha)
ring = ring.filter(ImageFilter.GaussianBlur(5))
glow = Image.new('RGBA', (width, frame_height), (120, 228, 255, 0))
glow.putalpha(ring)

# Arc geometry: run along the blade, from just above the guard to the tip.
left, top, right, bottom = box
span = right - left
arc = []
for t in (ARC_START, 0.45, 0.7, ARC_END):
    arc.append((left + t * span, bottom - t * span))
arc_x0, arc_y0 = arc[0]
arc_x1, arc_y1 = arc[-1]

strip = Image.new('RGBA', (width, frame_height * FRAMES), (0, 0, 0, 0))
for frame in range(FRAMES):
    rng = random.Random(0xA1C + frame * 7919)
    image = base.copy()

    # 1) rim glow, pulsing
    pulse = 0.45 + 0.4 * (0.5 + 0.5 * math.sin(frame / FRAMES * math.tau))
    layer = glow.copy()
    layer.putalpha(layer.getchannel('A').point(lambda v: int(v * pulse)))
    image = Image.alpha_composite(image, layer)

    # 2) lightning crawling over the blade
    bolts = Image.new('RGBA', (width, frame_height), (0, 0, 0, 0))
    pen = ImageDraw.Draw(bolts)
    for _ in range(ARC_COUNT):
        # each bolt picks its own sub-span so they do not all overlap
        a = rng.uniform(0.0, 0.45)
        b = rng.uniform(a + 0.35, 1.0)
        steps = 9
        points = []
        for i in range(steps + 1):
            t = a + (b - a) * i / steps
            px = arc_x0 + (arc_x1 - arc_x0) * t
            py = arc_y0 + (arc_y1 - arc_y0) * t
            # jitter perpendicular to the blade
            jitter = rng.uniform(-0.045, 0.045) * width
            points.append((px - jitter, py - jitter))
        pen.line(points, fill=(70, 190, 255, 150), width=max(3, width // 22), joint='curve')
        pen.line(points, fill=(255, 255, 255, 235), width=max(1, width // 64), joint='curve')

    # 3) a few free sparks near the blade
    for _ in range(3):
        t = rng.uniform(0.1, 1.0)
        px = arc_x0 + (arc_x1 - arc_x0) * t + rng.uniform(-0.05, 0.05) * width
        py = arc_y0 + (arc_y1 - arc_y0) * t + rng.uniform(-0.05, 0.05) * width
        r = max(1, width // 60)
        pen.ellipse([px - r, py - r, px + r, py + r], fill=(255, 255, 255, 230))

    # keep the lightning on the blade (plus a little bleed) instead of floating in mid air
    bleed = alpha.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(3))
    bolts.putalpha(ImageChops.multiply(bolts.getchannel('A'), bleed))
    image = Image.alpha_composite(image, bolts)

    strip.alpha_composite(image, (0, frame * frame_height))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
strip.save(OUT)
print('wrote %s (%dx%d, %d frames)' % (OUT, strip.width, strip.height, FRAMES))

# The animation descriptor has to exist next to the texture, otherwise Minecraft shows frame 0
# forever.
meta = os.path.join(os.path.dirname(OUT), 'lightning_sword.png.mcmeta')
with open(meta, 'w', encoding='utf-8') as handle:
    handle.write('{\n  "animation": {\n    "frametime": 2,\n    "interpolate": false\n  }\n}\n')
print('wrote', meta)
