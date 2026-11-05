# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

base = r"C:\Users\Jim\AppData\Local\dsh-blender-rt"
outdir = r"C:\xmfls test\ds\xmfls-osm-model\_shots"


def font(sz):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


views = [("elev", "正立面（街道侧）"), ("34", "四分之三视角（你截图那一带）")]
F = font(34)
FS = font(26)

panels = []
for tag, title in views:
    a = Image.open(rf"{base}\before_{tag}.png").convert("RGB")
    b = Image.open(rf"{base}\final_{tag}.png").convert("RGB")
    panels.append((a, b, title))

W = max(max(a.width, b.width) for a, b, _ in panels)
H = sum(max(a.height, b.height) + 78 for a, b, _ in panels) + 30
sheet = Image.new("RGB", (W * 2 + 36, H), (252, 252, 252))
dr = ImageDraw.Draw(sheet)

y = 10
for a, b, title in panels:
    dr.text((8, y), title + "   —   改前（门卫房顶到 9.40 m，和横墙顶齐平成一大块）",
            fill=(178, 34, 34), font=FS)
    dr.text((W + 44, y), "改后（门卫房顶 5.60 m，压顶随之下移，横墙不动）",
            fill=(20, 120, 60), font=FS)
    sheet.paste(a, (0, y + 40))
    sheet.paste(b, (W + 36, y + 40))
    y += max(a.height, b.height) + 78

sheet.save(rf"{outdir}\gate_gh_cut_before_after.png")
print(sheet.size)

# 放大对比：只截门卫房那一块
za = Image.open(rf"{base}\before_34.png").convert("RGB").crop((330, 380, 800, 850)).resize((700, 700), Image.LANCZOS)
zb = Image.open(rf"{base}\final_34.png").convert("RGB").crop((330, 380, 800, 850)).resize((700, 700), Image.LANCZOS)
z = Image.new("RGB", (1440, 760), (252, 252, 252))
d2 = ImageDraw.Draw(z)
d2.text((10, 6), "改前", fill=(178, 34, 34), font=F)
d2.text((730, 6), "改后", fill=(20, 120, 60), font=F)
z.paste(za, (0, 52))
z.paste(zb, (730, 52))
z.save(rf"{outdir}\gate_gh_cut_zoom.png")
print("zoom ok")
