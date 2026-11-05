# -*- coding: utf-8 -*-
"""把 Google Earth 俯视图按模型坐标套网格，方便定位。"""
from PIL import Image, ImageDraw, ImageFont
import math

im = Image.open('_ref/aerial.png').convert('RGB')
scale = 5.36
# fountain world (244.32,-8.92) at aerial (250,235); aerial +y = world +y
def w2a(x, y):
    return (250 + (x-244.32)*scale, 235 + (y+8.92)*scale)

d = ImageDraw.Draw(im)
try:
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 12)
except Exception:
    font = None
for gx in range(190, 320, 10):
    p0 = w2a(gx, -50); p1 = w2a(gx, 60)
    d.line([p0, p1], fill=(255,0,0), width=1)
    d.text((p0[0]+1, 4), str(gx), fill=(255,255,0), font=font)
for gy in range(-50, 61, 10):
    p0 = w2a(190, gy); p1 = w2a(320, gy)
    d.line([p0, p1], fill=(0,120,255), width=1)
    d.text((2, p0[1]+1), str(gy), fill=(255,255,0), font=font)

# fountain outline + gate line
for r in (8.6,):
    d.ellipse([w2a(244.32-r, -8.92-r), w2a(244.32+r, -8.92+r)], outline=(255,0,255), width=2)
d.line([w2a(264.6,43.9), w2a(297.6,5.1)], fill=(0,255,0), width=2)
im.resize((im.width*2, im.height*2), Image.LANCZOS).save('_ref/crop/aerial_grid.png')
print('ok')
