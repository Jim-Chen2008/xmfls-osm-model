# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

base = r"C:\Users\Jim\AppData\Local\dsh-blender-rt"
ref = Image.open(r"C:\Users\Jim\.dsh\attachments\v1\objects\be\be724d5f85de10522d9ea5e8af507d69eaf3bf52d3ae1372c0ea67d9d2b1f9e2").convert("RGB")
cands = [("eb", "A  \u7aef\u58a9", (0.95, 0.10, 0.10)),
         ("cg", "B  \u8f66\u884c\u5c0f\u95e8", (0.98, 0.45, 0.0)),
         ("tb", "C  \u9ad8\u58a9", (0.10, 0.75, 0.25)),
         ("gh", "D  \u95e8\u536b\u623f", (0.10, 0.35, 0.95))]


def font(size):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


f = font(26)
fw = 900
# reference column scaled to height 900
rw = int(ref.width * 900 / ref.height)
ref_s = ref.resize((rw, 900), Image.LANCZOS)

cell_h = 450
sheet = Image.new("RGB", (rw + 900 * 2 + 40, 900 + 20), (245, 245, 245))
sheet.paste(ref_s, (0, 0))
for i, (tag, lab, col) in enumerate(cands):
    im = Image.open(rf"{base}\cand_{tag}_lab1.png").convert("RGB").resize((900, 450), Image.LANCZOS)
    x = rw + 20 + (i % 2) * 900
    y = (i // 2) * 450
    sheet.paste(im, (x, y))
    dr = ImageDraw.Draw(sheet)
    dr.rectangle([x + 8, y + 8, x + 8 + 30, y + 38], fill=tuple(int(c * 255) for c in col))
    dr.text((x + 46, y + 10), lab, fill=(255, 255, 255), font=f)
    dr.rectangle([x, y, x + 899, y + 449], outline=(120, 120, 120))
dr.text((10, 908), "\u5de6\uff1a\u4f60\u7684\u622a\u56fe\u3002\u53f3\u4fa7\u56db\u5f20\uff1a\u53ea\u628a\u5bf9\u5e94\u6784\u4ef6\u67d3\u6210\u7ea2/\u6a59/\u7eff/\u84dd\uff0c\u5176\u4f59\u7070\u3002",
        fill=(20, 20, 20), font=font(20))
sheet.save(r"C:\xmfls test\ds\xmfls-osm-model\_shots\gate_candidates.png")
print(sheet.size)
