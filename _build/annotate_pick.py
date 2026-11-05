# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

ref = Image.open(r"C:\Users\Jim\.dsh\attachments\v1\objects\be\be724d5f85de10522d9ea5e8af507d69eaf3bf52d3ae1372c0ea67d9d2b1f9e2").convert("RGB")
lab = Image.open(r"C:\Users\Jim\AppData\Local\dsh-blender-rt\lab1.png").convert("RGB")

H = 900
ref_s = ref.resize((int(ref.width * H / ref.height), H), Image.LANCZOS)
lab_s = lab.resize((int(lab.width * H / lab.height), H), Image.LANCZOS)

pad = 24
sheet = Image.new("RGB", (ref_s.width + lab_s.width + pad, H + 130), (250, 250, 250))
sheet.paste(ref_s, (0, 0))
sheet.paste(lab_s, (ref_s.width + pad, 0))


def font(size):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


dr = ImageDraw.Draw(sheet)
f = font(26)
items = [((0.10, 0.35, 0.95), "\u62db\u724c\u6a2a\u5899/\u5b57"),
         ((0.95, 0.20, 0.20), "\u95e8\u536b\u623f"),
         ((0.15, 0.80, 0.25), "\u9ad8\u58a9"),
         ((0.98, 0.90, 0.10), "\u8f66\u884c\u5c0f\u95e8"),
         ((0.90, 0.20, 0.90), "\u7aef\u58a9"),
         ((0.55, 0.35, 0.15), "\u8857\u9053\u5730\u9762")]
x, y = 14, H + 12
for col, name in items:
    rgb = tuple(int(c * 255) for c in col)
    dr.rectangle([x, y + 3, x + 34, y + 37], fill=rgb, outline=(60, 60, 60))
    dr.text((x + 44, y), name, fill=(20, 20, 20), font=f)
    x += 44 + int(dr.textlength(name, font=f)) + 26
dr.text((14, H + 62), "\u5de6\uff1a\u4f60\u7684\u622a\u56fe\uff08\u7ea2\u6846\uff09\u3002\u53f3\uff1a\u540c\u4e00\u6bb5\u5730\u65b9\u7684\u6784\u4ef6\u5206\u8272\u56fe\uff08\u5de6\u4fa7\u56fe\u4e3b\u7f16\u53f7\u7684\u7ea2\u5708\u4f4d\u7f6e\uff09\u3002",
        fill=(20, 20, 20), font=font(22))
sheet.save(r"C:\xmfls test\ds\xmfls-osm-model\_shots\gate_pick.png")
print(sheet.size)
