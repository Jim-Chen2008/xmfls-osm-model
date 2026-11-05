# -*- coding: utf-8 -*-
"""Procedural textures: fair-faced concrete panels, brick, paving."""
import os, random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

random.seed(7)
OUT = os.path.join(os.path.dirname(__file__), 'tex')
os.makedirs(OUT, exist_ok=True)


def noise_img(size, octaves=3, seed=1):
    rnd = random.Random(seed)
    total = np.zeros((size, size), dtype=np.float32)
    amp = 1.0
    norm = 0.0
    for o in range(octaves):
        cells = 2 ** (o + 2)
        small = np.array([[rnd.random() for _ in range(cells + 1)] for _ in range(cells + 1)], dtype=np.float32)
        xs = np.linspace(0, cells, size, endpoint=False)
        ys = np.linspace(0, cells, size, endpoint=False)
        x0 = xs.astype(int); y0 = ys.astype(int)
        fx = (xs - x0)[None, :]; fy = (ys - y0)[:, None]
        a = small[y0][:, x0]; b = small[y0][:, x0 + 1]
        c = small[y0 + 1][:, x0]; d = small[y0 + 1][:, x0 + 1]
        up = a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy
        total += up * amp
        norm += amp
        amp *= 0.5
    return total / norm


def concrete(size=1024, panels=4):
    base = np.array([188, 183, 173], dtype=np.float32)
    n1 = noise_img(size, 4, 11)
    n2 = noise_img(size, 2, 23)
    img = np.zeros((size, size, 3), dtype=np.float32)
    tone = 0.92 + 0.16 * n1
    fine = (n2 - 0.5) * 0.10
    for c in range(3):
        img[:, :, c] = base[c] * tone + fine * 25.5
    img = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im, 'RGBA')
    step = size // panels
    for i in range(panels):
        for j in range(panels):
            t = random.uniform(-7, 7)
            d.rectangle((i * step, j * step, (i + 1) * step, (j + 1) * step),
                        fill=(int(128 + t), int(128 + t), int(124 + t), 18))
    for k in range(panels + 1):
        p = min(k * step, size - 1)
        d.line([(p, 0), (p, size)], fill=(120, 116, 108, 235), width=3)
        d.line([(p + 2, 0), (p + 2, size)], fill=(214, 210, 201, 120), width=1)
        d.line([(0, p), (size, p)], fill=(120, 116, 108, 235), width=3)
        d.line([(0, p + 2), (size, p + 2)], fill=(214, 210, 201, 120), width=1)
    for _ in range(26):
        x = random.randint(0, size)
        y = random.randint(0, size // 2)
        w = random.randint(2, 7)
        h = random.randint(30, 220)
        a = random.randint(6, 16)
        d.rectangle((x, y, x + w, y + h), fill=(96, 92, 84, a))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    im.save(os.path.join(OUT, 'concrete.png'))
    print('concrete ok')


def brick(size=512):
    rnd = random.Random(5)
    im = Image.new('RGB', (size, size), (200, 172, 146))
    d = ImageDraw.Draw(im)
    rows, cols = 20, 5
    bh, bw = size // rows, size // cols
    for r in range(rows):
        off = (bw // 2) if r % 2 else 0
        for c in range(cols + 1):
            x0 = c * bw - off
            y0 = r * bh
            t = rnd.randint(-16, 14)
            d.rectangle((x0 + 2, y0 + 2, x0 + bw - 2, y0 + bh - 3),
                        fill=(200 + t, 172 + t, 146 + t))
    d.rectangle((0, 0, size - 1, size - 1), outline=(172, 168, 160), width=2)
    arr = np.array(im, dtype=np.float32)
    n = noise_img(size, 3, 33)
    arr += ((n - 0.5) * 16)[:, :, None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.4))
    im.save(os.path.join(OUT, 'brick.png'))
    print('brick ok')


def paving(size=512):
    im = Image.new('RGB', (size, size), (205, 198, 184))
    n = noise_img(size, 3, 77)
    arr = np.array(im, dtype=np.float32) + ((n - 0.5) * 22)[:, :, None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, size - 1, size - 1), outline=(160, 154, 142), width=3)
    im.save(os.path.join(OUT, 'paving.png'))
    print('paving ok')


def panel_white(size=1024):
    """White cladding: 2 x 4 panels per 4.8 m tile (panels 2.4 x 1.2 m)."""
    base = np.array([225, 224, 219], dtype=np.float32)
    n1 = noise_img(size, 4, 41)
    img = np.zeros((size, size, 3), dtype=np.float32)
    tone = 0.975 + 0.045 * n1
    for c in range(3):
        img[:, :, c] = base[c] * tone
    img = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im, 'RGBA')
    for i in range(5):
        x = min(i * (size // 4), size - 1)
        d.line([(x, 0), (x, size)], fill=(168, 167, 161, 245), width=4)
        d.line([(x + 1, 0), (x + 1, size)], fill=(248, 247, 243, 160), width=1)
    for j in range(5):
        y = min(j * (size // 4), size - 1)
        d.line([(0, y), (size, y)], fill=(168, 167, 161, 245), width=4)
        d.line([(0, y + 1), (size, y + 1)], fill=(248, 247, 243, 160), width=1)
    im = im.filter(ImageFilter.GaussianBlur(0.5))
    im.save(os.path.join(OUT, 'panel_white.png'))
    print('panel ok')


def plaza(size=512):
    """8x8 stone tiles per 11.6 m（1.45 m 砖），细缝 + 每 4 砖一道深色分格带（5.8 m）。

    依据 2026-10-27 航拍贴图比对：实景砖缝约 1.45 m、分格带约 5.8 m。
    """
    rnd = random.Random(91)
    im = Image.new('RGB', (size, size), (200, 193, 178))
    d = ImageDraw.Draw(im)
    step = size // 8
    for i in range(8):
        for j in range(8):
            t = rnd.randint(-8, 8)
            d.rectangle((i * step + 1, j * step + 1, (i + 1) * step - 2, (j + 1) * step - 2),
                        fill=(200 + t, 193 + t, 178 + t))
    for i in range(9):
        p = min(i * step, size - 1)
        d.line([(p, 0), (p, size)], fill=(128, 125, 118), width=1)
        d.line([(0, p), (size, p)], fill=(128, 125, 118), width=1)
    for i in (0, 4, 8):
        p = min(i * step, size - 1)
        d.line([(p, 0), (p, size)], fill=(98, 96, 92), width=3)
        d.line([(0, p), (size, p)], fill=(98, 96, 92), width=3)
    arr = np.array(im, dtype=np.float32)
    n = noise_img(size, 3, 55)
    arr += ((n - 0.5) * 14)[:, :, None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.35))
    im.save(os.path.join(OUT, 'plaza.png'))
    print('plaza ok')


if __name__ == '__main__':
    concrete()
    brick()
    paving()
    panel_white()
    plaza()
