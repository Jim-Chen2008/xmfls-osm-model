# -*- coding: utf-8 -*-
import base64, os, sys
p = os.path.join(os.path.dirname(__file__), '..', 'viewer', 'gate_campus.glb')
d = open(p, 'rb').read()
b = base64.b64encode(d).decode('ascii')
out = os.path.join(os.path.dirname(__file__), '..', 'viewer', 'model.b64.js')
with open(out, 'w', encoding='ascii') as f:
    f.write('window.__MODEL_B64="' + b + '";\n')
print('glb', len(d), 'b64js', os.path.getsize(out))
