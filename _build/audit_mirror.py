# -*- coding: utf-8 -*-
"""顶点级镜像审计：把每个 GATE 网格的顶点集按 x→-x 镜像，在全场景里找匹配对象。
不受命名规则影响（索引后缀、单件/成对都能覆盖）。"""
import bpy, json, os
from collections import Counter

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, '_build', 'xmfls_gate.blend'))


def vkey(ob, mirror=False):
    pts = []
    for v in ob.data.vertices:
        x, y, z = v.co
        if mirror:
            x = -x
        pts.append((round(x, 3), round(y, 3), round(z, 3)))
    return tuple(sorted(pts))


objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('GATE_')]
keys = {o.name: vkey(o) for o in objs}
mkeys = {o.name: vkey(o, mirror=True) for o in objs}
pool = Counter(keys.values())

matched, unpaired = [], []
used = Counter()
for o in objs:
    target = mkeys[o.name]
    if pool[target] - used[target] > 0:
        matched.append(o.name)
        used[target] += 1
        if target == keys[o.name]:
            pass
    else:
        unpaired.append(o)

# 未配对对象：检查自身是否镜像对称
detail = []
for o in unpaired:
    self_sym = keys[o.name] == mkeys[o.name]
    xs = [v.co.x for v in o.data.vertices]
    detail.append({'name': o.name, 'self_symmetric': self_sym,
                   'x': [round(min(xs), 3), round(max(xs), 3)]})

print('HEADLESS ' + json.dumps({
    'gate_meshes': len(objs),
    'mirror_matched': len(matched),
    'unpaired': detail,
}, ensure_ascii=False))
