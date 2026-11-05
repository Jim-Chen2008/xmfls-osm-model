# -*- coding: utf-8 -*-
"""对比 gate_campus.glb 与 xmfls_gate.blend 里 GATE_tb_r 的实际区间。"""
import bpy, json, os

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
out = {}

def scan(tag):
    d = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith('GATE_tb_r'):
            continue
        xs = [v.co.x for v in o.data.vertices]
        ys = [v.co.y for v in o.data.vertices]
        zs = [v.co.z for v in o.data.vertices]
        d[o.name] = {'x': [round(min(xs), 4), round(max(xs), 4)],
                     'y': [round(min(ys), 4), round(max(ys), 4)],
                     'z': [round(min(zs), 4), round(max(zs), 4)],
                     'verts': len(o.data.vertices), 'polys': len(o.data.polygons)}
    out[tag] = d

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'viewer', 'gate_campus.glb'))
scan('gate_campus.glb')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, '_build', 'xmfls_gate.blend'))
scan('xmfls_gate.blend')

print('HEADLESS ' + json.dumps(out, ensure_ascii=False))
