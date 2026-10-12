"""Turns the crystal art into the mod's animated thunder crystal texture.

Source:  tools/crystal_source.png   - the raw art (any square-ish size, soft background is fine)
Output:  assets/lightning_sword/textures/item/thunder_crystal.png
         + a matching .png.mcmeta

The static art already has a lightning burst inside it, so the animation keeps that as the base and
adds three things on top, redrawn every frame:

  * a cyan-white additive bloom over the bright core, pulsing,
  * fresh electric arcs crawling across the crystal body,
  * flickering sparks around the shards.

Run:  python tools/build_crystal_texture.py
"""
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(PROJECT, 'tools', 'crystal_source.png')
ASSETS = os.path.join(PROJECT, 'src', 'main', 'resources', 'assets', 'lightning_sword')
OUT = os.path.join(ASSETS, 'textures', 'item', 'thunder_crystal.png')

SIZE = 64
FRAMES = 8
# Anything fainter than this in the source is background haze, not art.
ALPHA_FLOOR = 24
# How many crawling arcs per frame.
ARC_COUNT = 3

if not os.path.exists(SOURCE):
    raise SystemExit('Missing %s - put the crystal art there first.' % SOURCE)

raw = Image.open(SOURCE).convert('RGBA')

# 1) drop the soft background, 2) crop to the art, 3) centre it in a square, 4) scale down
pixels = raw.load()
for y in range(raw.height):
    for x in range(raw.width):
        r, g, b, a = pixels[x, y]
        if a < ALPHA_FLOOR:
            pixels[x, y] = (r, g, b, 0)

box = raw.getchannel('A').point(lambda v: 255 if v else 0).getbbox()
if box is None:
    raise SystemExit('The crystal art is fully transparent.')
art = raw.crop(box)
side = max(art.size)
square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
square.paste(art, ((side - art.width) // 2, (side - art.height) // 2))
base = square.resize((SIZE, SIZE), Image.LANCZOS)
print('source %s cropped to %s, scaled to %dx%d' % (raw.size, box, SIZE, SIZE))

body = base.getchannel('A').point(lambda v: 255 if v > ALPHA_FLOOR else 0)
# Arcs are allowed to spill a few pixels past the silhouette, like real discharge.
bleed = body.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2))

# Core bloom source: only the very brightest pixels of the drawing, blurred a lot.
lum = base.convert('RGB').convert('L')
core = lum.point(lambda v: v if v > 205 else 0).filter(ImageFilter.GaussianBlur(5))


def add_glow(image, mask, strength=1.0):
    """Additive cyan-white bloom, keeps the original alpha. Kept gentle: the source art is
    already bright, so a heavy bloom just blows the crystal out to flat white."""
    r = mask.point(lambda v: min(255, int(v * 0.18 * strength)))
    g = mask.point(lambda v: min(255, int(v * 0.30 * strength)))
    b = mask.point(lambda v: min(255, int(v * 0.36 * strength)))
    added = ImageChops.add(image.convert('RGB'), Image.merge('RGB', (r, g, b)))
    return Image.merge('RGBA', (*added.split(), image.getchannel('A')))


strip = Image.new('RGBA', (SIZE, SIZE * FRAMES), (0, 0, 0, 0))
for frame in range(FRAMES):
    rng = random.Random(0xC0FFEE + frame * 7919)
    phase = frame / FRAMES * 6.283185

    image = base.copy()

    # 1) pulsing bloom over the embedded lightning
    pulse = 0.55 + 0.45 * (0.5 + 0.5 * __import__('math').sin(phase))
    image = add_glow(image, core.point(lambda v: int(v * pulse * 0.5)))

    # 2) fresh arcs crawling across the crystal
    bolts = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    pen = ImageDraw.Draw(bolts)
    for _ in range(ARC_COUNT):
        x0 = rng.uniform(0.15, 0.85) * SIZE
        y0 = rng.uniform(0.10, 0.45) * SIZE
        x1 = rng.uniform(0.15, 0.85) * SIZE
        y1 = rng.uniform(0.55, 0.92) * SIZE
        steps = 7
        points = []
        for i in range(steps + 1):
            t = i / steps
            jitter = rng.uniform(-0.05, 0.05) * SIZE
            points.append((x0 + (x1 - x0) * t + jitter, y0 + (y1 - y0) * t + jitter))
        pen.line(points, fill=(80, 190, 255, 110), width=2, joint='curve')
        pen.line(points, fill=(255, 255, 255, 200), width=1, joint='curve')

    # 3) sparks flickering around the shards
    for _ in range(4):
        sx = rng.uniform(0.08, 0.92) * SIZE
        sy = rng.uniform(0.08, 0.92) * SIZE
        r = rng.choice((1, 1, 2))
        pen.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 255, 255, rng.randint(160, 255)))

    bolts.putalpha(ImageChops.multiply(bolts.getchannel('A'), bleed))
    image = Image.alpha_composite(image, bolts)

    strip.alpha_composite(image, (0, frame * SIZE))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
strip.save(OUT)
print('wrote %s (%dx%d, %d frames)' % (OUT, strip.width, strip.height, FRAMES))

meta = os.path.join(os.path.dirname(OUT), 'thunder_crystal.png.mcmeta')
with open(meta, 'w', encoding='utf-8') as handle:
    handle.write('{\n  "animation": {\n    "frametime": 2,\n    "interpolate": false\n  }\n}\n')
print('wrote', meta)
