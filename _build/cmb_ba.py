# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

base = r"C:\Users\Jim\AppData\Local\dsh-blender-rt"


def font(sz):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


pairs = [("elev", "正立面"), ("34", "三分之四视角")]
tiles = []
for tag, name in pairs:
    a = Image.open(rf"{base}\before_{tag}.png").convert("RGB")
    b = Image.open(rf"{base}\after_{tag}.png").convert("RGB")
    tiles.append((a, b, name))

W = max(max(a.width, b.width) for a, b, _ in tiles)
rowh = sum(max(a.height, b.height) + 60 for a, b, _ in tiles) + 20
sheet = Image.new("RGB", (W * 2 + 30, rowh), (250, 250, 250))
dr = ImageDraw.Draw(sheet)
f = font(30)
fl = font(26)
y = 8
for a, b, name in tiles:
    dr.text((10, y), f"{name} · 改前", fill=(190, 40, 40), font=f)
    dr.text((W + 40, y), f"{name} · 改后", fill=(30, 130, 60), font=f)
    sheet.paste(a, (0, y + 45))
    sheet.paste(b, (W + 30, y + 45))
    y += max(a.height, b.height) + 65
sheet.save(r"C:\xmfls test\ds\xmfls-osm-model\_shots\gh_cut_before_after.png")
print(sheet.size)
