"""把平面的剑贴图变成"薄片式 3D"物品模型（只加正面 / 背面 / 一圈厚度）。

为什么这么做：`item/handheld` 的剑只有一个平面，侧面看就是一张纸的边 —— 第三人称正面
会看到前后两面之间透过去的缝，第一人称就像贴纸。这个脚本逐帧描出剑的实心轮廓，做成一块
真正的薄板：

    正面 (z = +t)   原画（不动）——按"轮廓矩形合并"铺出来，面数比逐像素少一个数量级
    背面 (z = -t)   镜像的原画，从背后看也是实的
    厚度            沿轮廓每个格子一条窄边（1 像素宽），做出侧看的厚度感

仍然只用**同一张** 8 帧动画贴图：Minecraft 的贴图动画是把新像素上传到同一个 sprite 区域，
UV 不会变，所以动画 / 辉光 / 资源包覆盖全部照旧。

Run:  python tools/gen_sword_model.py
"""

import json
import os

from PIL import Image

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(PROJECT, 'src', 'main', 'resources', 'assets', 'lightning_sword')
TEXTURE = os.path.join(ASSETS, 'textures', 'item', 'lightning_sword.png')
ITEM_MODELS = os.path.join(ASSETS, 'models', 'item')
OUT = os.path.join(ITEM_MODELS, 'lightning_sword.json')

# 轮廓格子边长（贴图像素）：1 = 全分辨率（面数最多），2 = 推荐，3~4 = 更省但更"方块"。
CELL = 2
# 正面 / 背面那两层的半厚，单位是模型单位（16 = 一格）。
HALF_THICKNESS = 1.0
# 剑尖处的厚度缩放，别让整把剑像块砖。
TIP_TAPER = 0.45
# alpha >= 这个值算实心轮廓（剑周围那圈柔和辉光不算）。
SOLID_ALPHA = 128
FRAMES = 8

DISPLAY = {
    'firstperson_righthand': {'rotation': [60, -45, 25], 'translation': [1.13, 3.2, 1.13], 'scale': [0.78, 0.78, 0.78]},
    'firstperson_lefthand': {'rotation': [60, 45, -25], 'translation': [1.13, 3.2, 1.13], 'scale': [0.78, 0.78, 0.78]},
    'thirdperson_righthand': {'rotation': [60, -45, 55], 'translation': [-1.0, 4.0, 0.5], 'scale': [0.85, 0.85, 0.85]},
    'thirdperson_lefthand': {'rotation': [60, 45, -55], 'translation': [-1.0, 4.0, 0.5], 'scale': [0.85, 0.85, 0.85]},
}


def load_frames():
    image = Image.open(TEXTURE).convert('RGBA')
    width, height = image.size
    frame_height = height // FRAMES
    return ([image.crop((0, i * frame_height, width, (i + 1) * frame_height)) for i in range(FRAMES)],
            width, frame_height)


def mask_of(frame):
    """二值轮廓：mask[row][col]，row 0 是贴图顶部。"""
    width, height = frame.size
    alpha = frame.getchannel('A')
    cols, rows = width // CELL, height // CELL
    mask = []
    for row in range(rows):
        line = []
        for col in range(cols):
            solid = 0
            for y in range(row * CELL, row * CELL + CELL):
                for x in range(col * CELL, col * CELL + CELL):
                    if alpha.getpixel((x, y)) >= SOLID_ALPHA:
                        solid += 1
            line.append(solid * 2 >= CELL * CELL)
        mask.append(line)
    return mask


def fill_holes(mask, rounds=1):
    rows, cols = len(mask), len(mask[0])
    for _ in range(rounds):
        new = [row[:] for row in mask]
        for row in range(rows):
            for col in range(cols):
                if mask[row][col]:
                    continue
                filled = 0
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        y, x = row + dy, col + dx
                        if 0 <= y < rows and 0 <= x < cols and mask[y][x]:
                            filled += 1
                if filled >= 14:
                    new[row][col] = True
        mask = new
    return mask


def drop_specks(mask, min_neighbours=1):
    rows, cols = len(mask), len(mask[0])
    out = [row[:] for row in mask]
    for row in range(rows):
        for col in range(cols):
            if not mask[row][col]:
                continue
            neighbours = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    y, x = row + dy, col + dx
                    if 0 <= y < rows and 0 <= x < cols and mask[y][x]:
                        neighbours += 1
            if neighbours < min_neighbours:
                out[row][col] = False
    return out


def rects_of(mask):
    """贪心矩形合并：把实心格子拼成尽量少的矩形 (col0, row0, col1, row1)。"""
    rows, cols = len(mask), len(mask[0])
    used = [[False] * cols for _ in range(rows)]
    out = []
    for row in range(rows):
        for col in range(cols):
            if used[row][col] or not mask[row][col]:
                continue
            width = 1
            while col + width < cols and mask[row][col + width] and not used[row][col + width]:
                width += 1
            height = 1
            while row + height < rows:
                if all(mask[row + height][col + x] and not used[row + height][col + x] for x in range(width)):
                    height += 1
                else:
                    break
            for dy in range(height):
                for dx in range(width):
                    used[row + dy][col + dx] = True
            out.append((col, row, width, height))
    return out


class Frame:
    def __init__(self, image, mask):
        self.image = image
        self.mask = mask
        self.rows, self.cols = len(mask), len(mask[0])
        self.tex_width, self.tex_height = image.size
        self.top = next(r for r in range(self.rows) if any(mask[r]))
        self.bottom = next(r for r in range(self.rows - 1, -1, -1) if any(mask[r]))
        self.left = min(c for r in range(self.rows) for c in range(self.cols) if mask[r][c])

    @property
    def upp(self):
        """每个贴图像素等于多少模型单位（一帧 = 16 模型单位）。"""
        return 16.0 / (self.rows * CELL)

    def x(self, col):
        """几何用**贴图的原始像素位置**换算，不做任何平移，这样和旧版平面模型逐点对齐。"""
        return col * CELL * self.upp

    def y(self, row):
        """row 的上边缘高度（贴图 row 0 在顶部，对应模型 y = 16）。"""
        return (self.tex_height // CELL - row) * CELL * self.upp

    def u(self, col):
        return col * CELL

    def v(self, row):
        return row * CELL

    def thickness(self, row):
        span = max(1, self.bottom - self.top)
        t = (self.bottom - row) / span
        return HALF_THICKNESS * (1.0 - t * (1.0 - TIP_TAPER))

    def edge_uv(self, row, col):
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return [(col + 0.5) * CELL, (row + 0.5) * CELL]


def faces(f):
    """正面 + 背面：按合并后的矩形铺。"""
    elements = []
    for col0, row0, width, height in rects_of(f.mask):
        x0 = f.x(col0)
        x1 = f.x(col0 + width)
        y1 = f.y(row0)
        y0 = f.y(row0 + height)
        u0, u1 = f.u(col0), f.u(col0 + width)
        v0, v1 = f.v(row0), f.v(row0 + height)
        t = max(f.thickness(row0), f.thickness(row0 + height - 1))
        elements.append({
            'from': [x0, y0, 0.0], 'to': [x1, y1, t],
            'faces': {'north': {'uv': [u0, v0, u1, v1], 'texture': '#layer0'}},
        })
        elements.append({
            'from': [x0, y0, -t], 'to': [x1, y1, 0.0],
            'faces': {'south': {'uv': [u1, v0, u0, v1], 'texture': '#layer0'}},
        })
    return elements


def thickness_quads(f):
    """厚度：轮廓上每个暴露的格子边一条窄面（1 像素宽），取边缘像素颜色。"""
    mask = f.mask
    rows, cols = f.rows, f.cols
    elements = []

    def strip(x0, x1, y0, y1, t, face, uv):
        elements.append({
            'from': [x0, y0, -t], 'to': [x1, y1, t],
            'faces': {face: {'uv': uv, 'texture': '#layer0'}},
        })

    for row in range(rows):
        for col in range(cols):
            if not mask[row][col]:
                continue
            t = f.thickness(row)
            y0 = f.y(row) - CELL * f.upp
            y1 = f.y(row)
            sliver = CELL * f.upp * 0.4
            left_open = col == 0 or not mask[row][col - 1]
            right_open = col + 1 >= cols or not mask[row][col + 1]
            top_open = row == 0 or not mask[row - 1][col]
            bottom_open = row + 1 >= rows or not mask[row + 1][col]
            if left_open:
                u, v = f.edge_uv(row, col)
                strip(f.x(col), f.x(col) + sliver, y0, y1, t, 'west', [u, v, u, v])
            if right_open:
                u, v = f.edge_uv(row, col)
                strip(f.x(col + 1) - sliver, f.x(col + 1), y0, y1, t, 'east', [u, v, u, v])
            if top_open:
                u, v = f.edge_uv(row, col)
                strip(f.x(col), f.x(col + 1), y1 - sliver, y1, t, 'up', [u, v, u, v])
            if bottom_open:
                u, v = f.edge_uv(row, col)
                strip(f.x(col), f.x(col + 1), y0, y0 + sliver, t, 'down', [u, v, u, v])
    return elements


def main():
    frames, tex_width, frame_height = load_frames()
    all_elements = []
    for index, frame_image in enumerate(frames):
        mask = fill_holes(drop_specks(mask_of(frame_image)))
        f = Frame(frame_image, mask)
        solid = sum(sum(1 for cell in row if cell) for row in mask)
        rects = rects_of(mask)
        elements = faces(f) + thickness_quads(f)
        all_elements.extend(elements)
        print('frame %d: 实心格子 %d，合并成 %d 个矩形，几何面 %d' % (index, solid, len(rects), len(elements)))

    model = {
        'parent': 'minecraft:item/handheld',
        'textures': {
            'layer0': 'lightning_sword:item/lightning_sword',
            'particle': 'lightning_sword:item/lightning_sword',
        },
        'texture_size': [tex_width, frame_height],
        'elements': all_elements,
        'display': DISPLAY,
    }
    os.makedirs(ITEM_MODELS, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as handle:
        json.dump(model, handle, separators=(',', ':'))
    print('写出 %s（%.1f KB，%d 个面）' % (OUT, os.path.getsize(OUT) / 1024.0, len(all_elements)))


if __name__ == '__main__':
    main()
