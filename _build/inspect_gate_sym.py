# -*- coding: utf-8 -*-
"""检查 GATE 段左右镜像对称性：以 GATE_ROOT 局部 x=0 为镜面，
逐个对比 X 同名对象（后缀 _1 / _-1）的 x 区间是否互为镜像。"""
import bpy, json, os, sys

argv = sys.argv
glb = None
for i, a in enumerate(argv):
    if a == '--' and i + 1 < len(argv):
        glb = argv[i + 1]
if not glb:
    glb = r"C:\xmfls test\ds\xmfls-osm-model\viewer\gate_campus - 副本.glb"

bpy.ops.import_scene.gltf(filepath=glb)

bounds = {}
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith('GATE_'):
        continue
    if not o.data.vertices:
        continue
    xs = [v.co.x for v in o.data.vertices]
    bounds[o.name] = (round(min(xs), 4), round(max(xs), 4))

pairs, unpaired, bad = {}, [], []
for name, (lo, hi) in sorted(bounds.items()):
    if not name.endswith('_1'):
        continue
    base = name[:-2]
    other = base + '_-1'
    if other not in bounds:
        unpaired.append(name)
        continue
    olo, ohi = bounds[other]
    pair = {'base': base, 'pos_x': [lo, hi], 'neg_x': [olo, ohi],
            'mirror_err': round(max(abs(lo + ohi), abs(hi + olo)), 4)}
    pairs[base] = pair
    if pair['mirror_err'] > 0.002:
        bad.append(pair)

report = {
    'glb': os.path.basename(glb),
    'gate_meshes': len(bounds),
    'tb_objects': {k: v for k, v in bounds.items() if 'tb_' in k},
    'asymmetric': bad,
    'unpaired': unpaired,
}
print('HEADLESS ' + json.dumps(report, ensure_ascii=False))
