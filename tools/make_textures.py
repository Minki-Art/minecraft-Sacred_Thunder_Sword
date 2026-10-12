"""Generates every texture the mod ships.

  * textures/item/lightning_sword.png  - an 8 frame animated strip (16x16 per frame, 16x128)
  * textures/block/lightning_ore.png   - the lightning ore block face
  * icon.png                           - the 128x128 mod icon

Paths are derived from this file's location (<project>/tools/make_textures.py), so the project
can be moved or renamed freely.

Run:  python tools/make_textures.py
"""
import math
import os
import random
from PIL import Image, ImageChops, ImageDraw, ImageFilter

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(PROJECT, 'src', 'main', 'resources', 'assets', 'lightning_sword')
FRAMES = 8

os.makedirs(os.path.join(ROOT, 'textures', 'item'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'textures', 'block'), exist_ok=True)

# ---------------------------------------------------------------- sword

# 16 rows of 16 chars.  '.' = transparent
ART = [
    "................",
    ".............EE.",
    "............hBEE",
    "...........hBBb.",
    "..........hBBb..",
    ".........hBBb...",
    "........hBBb....",
    ".......hBBb.....",
    "......hBBb......",
    ".....hBBb.......",
    "....GGGBb.......",
    "...GGGGb........",
    "..KHHGG.........",
    "..KHHK..........",
    ".KHHK...........",
    ".KK.............",
]

PALETTE = {
    'h': (255, 255, 255, 255),   # blade leading edge: a bright white rim
    'B': (196, 236, 252, 255),   # blade body: pale ice
    'b': (112, 180, 224, 255),   # blade shadow
    'E': (255, 250, 170, 255),   # spark
    'G': (255, 212, 74, 255),    # gold guard
    'g': (186, 140, 28, 255),    # dark gold
    'H': (108, 68, 40, 255),     # handle
    'K': (66, 39, 21, 255),      # handle shadow
}

assert len(ART) == 16, len(ART)
base = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
pixels = base.load()
for y, row in enumerate(ART):
    assert len(row) == 16, (y, len(row), row)
    for x, ch in enumerate(row):
        if ch != '.':
            pixels[x, y] = PALETTE[ch]

# Blade pixels ordered from the guard to the tip. Everything below works along this path, so
# the filaments follow the blade instead of scattering over the sprite.
BLADE_PATH = sorted(
    ((x, y) for y, row in enumerate(ART) for x, ch in enumerate(row) if ch in 'hB'),
    key=lambda p: (p[0] + (15 - p[1])),
)
ARC = (255, 255, 255, 255)        # the filament itself
HALO = (150, 232, 255, 255)       # cyan bleed around a filament
ARC_SHADOW = (44, 104, 164, 255)  # dark notch that makes the filament pop
SPARK = (255, 246, 190, 255)

strip = Image.new('RGBA', (16, 16 * FRAMES), (0, 0, 0, 0))
for frame in range(FRAMES):
    img = base.copy()
    rng = random.Random(0x51F + frame * 7919)

    # Three short filaments crawling along the blade, redrawn every frame. Each one is a white
    # core with a cyan bleed and a dark notch on either end, which is what reads as an electric
    # arc instead of a fat white bar at this size.
    for _ in range(3):
        start = rng.randrange(len(BLADE_PATH))
        run = rng.randint(4, 7)
        for k in range(run):
            img.putpixel(BLADE_PATH[(start + k) % len(BLADE_PATH)], ARC)
        img.putpixel(BLADE_PATH[(start - 1) % len(BLADE_PATH)], HALO)
        img.putpixel(BLADE_PATH[(start - 2) % len(BLADE_PATH)], ARC_SHADOW)
        img.putpixel(BLADE_PATH[(start + run) % len(BLADE_PATH)], ARC_SHADOW)

    # Dancing tip sparks.
    for index, point in enumerate([(13, 1), (14, 2), (13, 2), (14, 1), (12, 1)]):
        if (index + frame) % 2 == 0:
            img.putpixel(point, ARC)
        elif (index + frame) % 3 == 0:
            img.putpixel(point, HALO)

    # A spark crawling over the guard.
    img.putpixel([(4, 10), (3, 11), (5, 10), (2, 12)][frame % 4], SPARK)

    strip.alpha_composite(img, (0, frame * 16))

item_path = os.path.join(ROOT, 'textures', 'item', 'lightning_sword.png')
if os.path.exists(os.path.join(PROJECT, 'tools', 'sword_source.png')):
    # build_sword_texture.py owns this file whenever there is real art to build from. Writing the
    # pixel-art fallback here would silently clobber it.
    print('skipped %s - tools/sword_source.png exists, run build_sword_texture.py' % item_path)
else:
    strip.save(item_path)
    print('wrote %s (%dx%d, %d frames, pixel-art fallback)'
          % (item_path, strip.width, strip.height, FRAMES))

# ---------------------------------------------------------------- thunder crystal
#
# A single gem sprite, the way diamond is an item rather than an ore block.
# "Hexagonal crystal, longer on the top / bottom / left / right sides": the silhouette below is a
# pointy-top hexagon - one pixel at the very top and bottom, and four rows of full width in the
# middle so the left and right sides are long and flat.

CRYSTAL = {
    'glint': (255, 255, 255, 255),
    'light': (200, 250, 255, 255),
    'mid': (104, 214, 248, 255),
    'dark': (44, 138, 200, 255),
    'outline': (12, 48, 88, 255),
}

# Half width of the gem on each of the 16 rows. 0 = a single pixel point.
# Max 6 rather than 7 so the left and right edges keep a one pixel margin for the outline.
CRYSTAL_PROFILE = [0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 5, 4, 3, 2, 1, 0]
CRYSTAL_CENTER = 7.5
CRYSTAL_RADIUS = 7.5

crystal = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
cp = crystal.load()
for y, half_width in enumerate(CRYSTAL_PROFILE):
    for x in range(16):
        if abs((x + 0.5) - CRYSTAL_CENTER) > half_width:
            continue
        nx = ((x + 0.5) - CRYSTAL_CENTER) / CRYSTAL_RADIUS
        ny = ((y + 0.5) - CRYSTAL_CENTER) / CRYSTAL_RADIUS
        # one diagonal split gives the classic two-facet gem look at this size
        if nx + ny < -0.45:
            colour = CRYSTAL['light']      # lit upper-left facet
        elif nx + ny > 0.45:
            colour = CRYSTAL['dark']       # shadowed lower-right facet
        else:
            colour = CRYSTAL['mid']
        cp[x, y] = colour

# one small highlight on the upper-left shoulder
for glint in ((4, 3), (5, 3), (4, 4)):
    cp[glint[0], glint[1]] = CRYSTAL['glint']

# 1px outline hugging the gem. Only the four orthogonal neighbours, otherwise the diagonal
# dilation blunts the single-pixel tip. Computed from a frozen set of the mask, so writing the
# outline cannot feed back into itself.
solid = {(x, y) for y in range(16) for x in range(16) if cp[x, y][3]}
outline = set()
for (x, y) in solid:
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < 16 and 0 <= ny < 16 and (nx, ny) not in solid:
            outline.add((nx, ny))
for (x, y) in outline:
    cp[x, y] = CRYSTAL['outline']

crystal_path = os.path.join(ROOT, 'textures', 'item', 'thunder_crystal.png')
if os.path.exists(os.path.join(PROJECT, 'tools', 'crystal_source.png')):
    print('skipped %s - tools/crystal_source.png exists, run build_crystal_texture.py' % crystal_path)
else:
    crystal.save(crystal_path)
    print('wrote %s (16x16, pixel-art fallback)' % crystal_path)

# ---------------------------------------------------------------- mod icon

ICON = 128
icon = Image.new('RGBA', (ICON, ICON), (14, 22, 40, 255))
draw = ImageDraw.Draw(icon)
for i in range(ICON):
    shade = int(14 + 34 * (i / (ICON - 1)))
    draw.line([(0, i), (ICON, i)], fill=(shade // 2, shade, min(255, shade + 40), 255))

for points, colour in [
    ([(12, 6), (24, 34), (16, 36), (34, 74)], (120, 210, 255, 190)),
    ([(112, 10), (98, 40), (108, 42), (88, 86)], (120, 210, 255, 150)),
]:
    draw.line(points, fill=colour, width=3, joint='curve')

icon.alpha_composite(base.resize((96, 96), Image.NEAREST), (16, 16))
icon_path = os.path.join(ROOT, 'icon.png')
icon.save(icon_path)
print('wrote', icon_path)
