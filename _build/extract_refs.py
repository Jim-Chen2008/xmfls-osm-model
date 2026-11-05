# -*- coding: utf-8 -*-
import re, base64, os
p = r"C:\xmfls test\ds\xmfls-osm-model\viewer\refs.js"
s = open(p, encoding="utf-8").read()
print("len", len(s))
print(s[:200])
outdir = r"C:\xmfls test\ds\xmfls-osm-model\_ref\from_js"
os.makedirs(outdir, exist_ok=True)
# find  data:image/xxx;base64,.....
for m in re.finditer(r"data:image/(png|jpeg|jpg);base64,([A-Za-z0-9+/=]+)", s):
    ext = "png" if m.group(1) == "png" else "jpg"
    data = base64.b64decode(m.group(2))
    start = max(0, m.start() - 200)
    ctx = s[start:m.start()].replace("\n", " ")[-120:]
    name = re.sub(r"[^A-Za-z0-9_]+", "_", ctx)[-40:]
    fn = os.path.join(outdir, f"{name or 'img'}_{m.start()}.{ext}")
    open(fn, "wb").write(data)
    print("wrote", fn, len(data))
