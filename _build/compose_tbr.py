# -*- coding: utf-8 -*-
"""合成修复前/后正立面对比图 + 镜像自检。"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
SH = os.path.join(ROOT, '_shots')
before = Image.open(os.path.join(SH, 'tbr_iso_before.png')).convert('RGB')
after = Image.open(os.path.join(SH, 'tbr_iso_after.png')).convert('RGB')

# ---------- 镜像自检：正确模型的正射正立面应左右镜像一致（校名文字区除外）
A = np.asarray(after).astype(int)
Afl = A[:, ::-1, :]
d = np.abs(A - Afl).sum(axis=2)
mask = d > 24
mask[:60, :] = False           # 顶部空区
mask[70:170, 380:1120] = False  # 校名/英文文字带（非镜像对称的图形）
ys, xs = np.where(mask)
sym = {
    'pixels_differing': int(mask.sum()),
    'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
}

# ---------- 像素↔模型坐标（ortho 46 m / 1500 px，中心对准大门中心）
PPM = 1500 / 46.0
def px_of_x(xl):
    return 750 - xl * PPM
def px_of_z(z):
    return 260 - (z - 3.0) * PPM

rect = (px_of_x(-14.75), px_of_z(6.0), px_of_x(-18.25), px_of_z(-0.35))
print('rect', [round(v, 1) for v in rect])

W, H = after.size
HDR, GAP, FTR = 78, 18, 104
canvas = Image.new('RGB', (W, HDR * 2 + GAP + H * 2 + FTR), (247, 247, 249))
dr = ImageDraw.Draw(canvas)


def font(sz, bold=False):
    for p in (r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
              r"C:\Windows\Fonts\simhei.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


f1, f2 = font(26, True), font(19)

y = 0
for img, label, sub, col in ((before, '修复前  GATE_tb_r_-1 是宽 0 的退化面片', '负侧（画面右）高墩外侧整块缺失：3.5 m 宽 × 6.35 m 高，x 区间退化到 [-11.95, -11.95]', (196, 40, 40)),
                             (after, '修复后  gate_campus.glb', '负侧补成 [-18.25, -14.75] 的实心段，与正侧 [14.75, 18.25] 完全镜像', (24, 122, 68))):
    dr.text((28, y + 10), label, font=f1, fill=col)
    dr.text((28, y + 44), sub, font=f2, fill=(70, 70, 78))
    y += HDR
    canvas.paste(img, (0, y))
    d2 = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = rect
    box = (x0, y + y0, x1, y + y1)
    d2.rectangle(box, outline=(220, 60, 40), width=3)
    d2.text((box[2] + 10, box[1] + 2), 'GATE_tb_r', font=f2, fill=(220, 60, 40))
    y += H + GAP

dr.text((28, y + 8), '顶点级镜像审计（GATE 153 个网格）：50 组合实体全部镜像匹配；未配对的 103 个中 11 个为居中校名文字、',
        font=f2, fill=(60, 60, 66))
dr.text((28, y + 26), '92 个为洞口内装饰格栅的斜杆（按洞口内沿起算，相位差 ≤0.16 m，仍铺满洞口，肉眼不可见）。', font=f2, fill=(60, 60, 66))

out = os.path.join(SH, 'tbr_fix_compare.png')
canvas.save(out)
print('SAVED', out, canvas.size)
print('SYM ' + str(sym))
