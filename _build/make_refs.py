# -*- coding: utf-8 -*-
import base64, io, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'viewer', 'refs.js')

def data_uri(im, w=980, q=80):
    im = im.convert('RGB')
    if im.width > w:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=q, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')

refs = {}

# 1. 街道立面（老照片里的金字正立面）
im = Image.open(os.path.join(ROOT, '_ref', 'gate_front.jpg'))
refs['street'] = data_uri(im.crop((20, 1020, 1140, 1580)), 980, 82)

# 2. 新照片：大门近景
im = Image.open(os.path.join(ROOT, '_ref', 'new_gate_dsc06233.jpg'))
refs['gate'] = data_uri(im, 980, 82)

# 3. 新照片：广场 + 喷泉花圃
im = Image.open(os.path.join(ROOT, '_ref', 'new_overview.jpg'))
refs['bed'] = data_uri(im.crop((650, 560, 1700, 1400)), 980, 82)

# 4. 俯视实景（喷泉与花圃）
im = Image.open(os.path.join(ROOT, '_ref', 'aerial.png'))
refs['aerial'] = data_uri(im, 660, 85)

with open(OUT, 'w', encoding='ascii') as f:
    f.write('window.__REFS = {\n')
    for k, v in refs.items():
        f.write('  %s: "%s",\n' % (k, v))
    f.write('};\n')
print('refs.js', os.path.getsize(OUT), {k: len(v) // 1024 for k, v in refs.items()})
