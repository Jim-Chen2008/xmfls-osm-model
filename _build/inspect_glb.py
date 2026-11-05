# -*- coding: utf-8 -*-
import json, struct, sys, os, math

def load_glb(p):
    d = open(p, 'rb').read()
    assert d[:4] == b'glTF'
    off = 12
    js = None; bin_ = None
    while off < len(d):
        ln, ty = struct.unpack_from('<II', d, off)
        chunk = d[off+8:off+8+ln]
        if ty == 0x4E4F534A:
            js = json.loads(chunk.decode('utf-8'))
        elif ty == 0x004E4942:
            bin_ = chunk
        off += 8 + ln
    return js, bin_

p = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Jim\Downloads\厦门外国语学校（海沧校区）-edited-20261027-1632-edited-20261027-1659.glb'
j, bin_ = load_glb(p)
print('nodes', len(j.get('nodes', [])), 'meshes', len(j.get('meshes', [])), 'materials', len(j.get('materials', [])))
print('scenes', j.get('scenes'))
print('asset', j.get('asset'))
print('--- materials ---')
for i, m in enumerate(j.get('materials', [])):
    pbr = m.get('pbrMetallicRoughness', {})
    print(i, m.get('name'), pbr.get('baseColorFactor'), 'tex' if 'baseColorTexture' in pbr else '')

print('--- nodes ---')
for i, n in enumerate(j.get('nodes', [])):
    print(i, repr(n.get('name')), 'mesh=', n.get('mesh'), 'children=', n.get('children'),
          'T=', n.get('translation'), 'R=', n.get('rotation'), 'S=', n.get('scale'), 'M=', 'yes' if 'matrix' in n else '')
