"""离线检查 gen_sword_model.py 生成的物品模型。

它做三件事：
  1. 结构校验：坐标 / UV 是否在合法范围、每个面是否有合法朝向
  2. 把第 0 帧的几何按等轴投影画成图（tools/model_preview.png），确认"薄板 + 厚度"真的成立

Run:  python tools/preview_sword_model.py
"""

import json
import math
import os

from PIL import Image, ImageDraw

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(PROJECT, 'src', 'main', 'resources', 'assets', 'lightning_sword')
MODEL = os.path.join(ASSETS, 'models', 'item', 'lightning_sword.json')
TEXTURE = os.path.join(ASSETS, 'textures', 'item', 'lightning_sword.png')
OUT = os.path.join(PROJECT, 'tools', 'model_preview.png')

FACES = ('north', 'south', 'east', 'west', 'up', 'down')
# 等轴投影（x 向右，y 向上，z 表示厚度方向）
SCALE = 9
COS_A, SIN_A = math.cos(math.radians(30)), math.sin(math.radians(30))


def project(x, y, z):
    sx = (x * COS_A + z * SIN_A) * SCALE
    sy = (-y + (z * COS_A - x * SIN_A) * 0.0) * SCALE
    return sx, sy


def main():
    raw = open(MODEL, encoding='utf-8').read()
    model = json.loads(raw)
    elements = model['elements']
    tex_w, tex_h = model['texture_size']
    print('元素 %d，贴图单元 %dx%d，%.1f KB' % (len(elements), tex_w, tex_h, len(raw) / 1024.0))

    problems = []
    xs, ys, zs = [], [], []
    for index, element in enumerate(elements):
        x0, y0, z0 = element['from']
        x1, y1, z1 = element['to']
        if not (x0 < x1 and y0 < y1 and z0 < z1):
            problems.append('元素 %d: from/to 不是递增的 %s -> %s' % (index, element['from'], element['to']))
        for value in (x0, x1, y0, y1, z0, z1):
            if value < -16.0 or value > 32.0:
                problems.append('元素 %d: 坐标越界 %s' % (index, value))
        xs += [x0, x1]
        ys += [y0, y1]
        zs += [z0, z1]
        for face_name, face in element['faces'].items():
            if face_name not in FACES:
                problems.append('元素 %d: 非法面 %s' % (index, face_name))
            uv = face.get('uv')
            if uv is None or len(uv) != 4:
                problems.append('元素 %d: uv 不是 4 个值' % index)
            if face.get('texture') != '#layer0':
                problems.append('元素 %d: 纹理引用异常' % index)

    print('包围盒 x[%.2f, %.2f]  y[%.2f, %.2f]  z[%.2f, %.2f]'
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print('包围盒尺寸 %.2f x %.2f x %.2f 模型单位（应为 16 x 16 左右）'
          % (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    print('半厚 %.2f 模型单位 = 贴图 %.1f 像素' % (max(zs), (max(zs)) * tex_w / 16.0))
    print('问题数:', len(problems))
    for problem in problems[:10]:
        print('  ', problem)

    # ---- 预览第 0 帧 ----
    frame_height = tex_h
    texture = Image.open(TEXTURE).convert('RGBA').crop((0, 0, tex_w, frame_height))
    image = Image.new('RGBA', (520, 340), (24, 24, 30, 255))
    draw = ImageDraw.Draw(image)
    ox, oy = 60, 300

    def to_screen(x, y, z):
        sx, sy = project(x, y, z)
        return ox + sx, oy + sy

    # 只画前 200 个元素，够看清结构；先按 z 从小到大画（远 -> 近）
    selected = elements[:200]
    selected.sort(key=lambda element: (element['from'][2] + element['to'][2]) / 2)
    for element in selected:
        x0, y0, z0 = element['from']
        x1, y1, z1 = element['to']
        for face_name, face in element['faces'].items():
            uv = face['uv']
            u = sum(uv[0::2]) / 2
            v = sum(uv[1::2]) / 2
            u = max(0, min(int(u), tex_w - 1))
            v = max(0, min(int(v), frame_height - 1))
            r, g, b, a = texture.getpixel((u, v))
            if a < 8:
                continue
            shade = {'north': 1.0, 'south': 0.55, 'east': 0.7, 'west': 0.85, 'up': 1.15, 'down': 0.5}[face_name]
            colour = (min(255, int(r * shade)), min(255, int(g * shade)), min(255, int(b * shade)), 255)
            corners = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]
            if 'north' in element['faces'] and face_name == 'north':
                points = [to_screen(*corner) for corner in corners]
            elif face_name == 'south':
                points = [to_screen(x0, y0, z1), to_screen(x1, y0, z1), to_screen(x1, y1, z1), to_screen(x0, y1, z1)]
            else:
                points = [to_screen(x0, y0, z0), to_screen(x1, y0, z0)]
            if len(points) == 4:
                draw.polygon(points, fill=colour)

    image.convert('RGB').save(OUT)
    print('等轴预览写出', OUT)

    # ---- 纯正面视图：直接按 UV 采样贴图，用来确认几何和贴图对得上 ----
    front = Image.new('RGBA', (tex_w, frame_height), (0, 0, 0, 0))
    pixel = front.load()
    for element in elements:
        face = element['faces'].get('north')
        if face is None:
            continue
        x0, y0, _ = element['from']
        x1, y1, _ = element['to']
        u0, v0, u1, v1 = face['uv']
        px0 = int(round((x0 + 8.0) * tex_w / 16.0))
        px1 = int(round((x1 + 8.0) * tex_w / 16.0))
        py0 = int(round((8.0 - y1) * frame_height / 16.0))
        py1 = int(round((8.0 - y0) * frame_height / 16.0))
        for py in range(max(0, py0), min(frame_height, py1)):
            tv = v0 + (v1 - v0) * ((py - py0) / max(1, py1 - py0))
            for px in range(max(0, px0), min(tex_w, px1)):
                tu = u0 + (u1 - u0) * ((px - px0) / max(1, px1 - px0))
                tu = max(0, min(int(tu), tex_w - 1))
                tv = max(0, min(int(tv), frame_height - 1))
                r, g, b, a = texture.getpixel((tu, tv))
                if a > 0:
                    pixel[px, py] = (r, g, b, 255)
    front_out = os.path.join(PROJECT, 'tools', 'model_front.png')
    front.convert('RGB').save(front_out)
    print('正面校验图写出', front_out)


if __name__ == '__main__':
    main()
