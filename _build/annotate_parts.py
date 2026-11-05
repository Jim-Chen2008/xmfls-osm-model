# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

A = Image.open(r"C:\Users\Jim\AppData\Local\dsh-blender-rt\lab1.png").convert("RGB")
B = Image.open(r"C:\Users\Jim\AppData\Local\dsh-blender-rt\lab2.png").convert("RGB")
W, H = A.size
sheet = Image.new("RGB", (W * 2, H + 150), (245, 245, 245))
sheet.paste(A, (0, 0))
sheet.paste(B, (W, 0))
dr = ImageDraw.Draw(sheet)

def font(size):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

f = font(22)
items = [
    ((0.12, 0.30, 0.95), "招牌横墙 / 字 / 门洞栏杆"),
    ((0.95, 0.20, 0.20), "门卫房"),
    ((0.15, 0.80, 0.25), "高墩"),
    ((0.98, 0.90, 0.10), "车行小门"),
    ((0.90, 0.20, 0.90), "端墩"),
    ((0.55, 0.35, 0.15), "街道地面"),
]
x = 16
y = H + 18
for col, lab in items:
    rgb = tuple(int(c * 255) for c in col)
    dr.rectangle([x, y + 4, x + 30, y + 30], fill=rgb)
    dr.text((x + 40, y), lab, fill=(20, 20, 20), font=f)
    x += 40 + int(dr.textlength(lab, font=f)) + 34
dr.text((16, H + 60), "左图：从 +u 端（东南）看；右图：从 -u 端（西北）看。请指出红色标注框里那一坨对应哪种颜色。",
        fill=(20, 20, 20), font=f)
sheet.save(r"C:\xmfls test\ds\xmfls-osm-model\_shots\gate_labeled.png")
print(sheet.size)
