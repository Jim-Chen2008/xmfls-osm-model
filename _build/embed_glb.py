# -*- coding: utf-8 -*-
"""Embed the given GLB into viewer/model.b64.js (the file index.html loads)."""
import base64, os, shutil, sys

src = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Jim\Downloads\gate_campus_new-edited-20261027-2212.glb"
root = r"C:\xmfls test\ds\xmfls-osm-model"
dst_glb = os.path.join(root, 'viewer', 'gate_campus.glb')
# keep a copy of the exact source next to the viewer
shutil.copyfile(src, os.path.join(root, 'viewer', 'gate_campus_current.glb'))
data = open(src, 'rb').read()
b64 = base64.b64encode(data).decode('ascii')
out = os.path.join(root, 'viewer', 'model.b64.js')
with open(out, 'w', encoding='ascii') as f:
    f.write('window.__MODEL_B64="' + b64 + '";\n')
print('src bytes', len(data), 'b64js', os.path.getsize(out))
