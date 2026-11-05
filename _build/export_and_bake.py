# -*- coding: utf-8 -*-
"""把修好的 xmfls_gate.blend 导出为 viewer/gate_campus.glb，并重建 model.b64.js。"""
import bpy, base64, os

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
src = os.path.join(ROOT, '_build', 'xmfls_gate.blend')
out = os.path.join(ROOT, 'viewer', 'gate_campus.glb')

bpy.ops.wm.open_mainfile(filepath=src)
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print('pack warn', e)

bpy.ops.export_scene.gltf(
    filepath=out,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_yup=True,
    export_materials='EXPORT',
    export_texcoords=True,
    export_normals=True,
)

data = open(out, 'rb').read()
b64 = base64.b64encode(data).decode('ascii')
b64p = os.path.join(ROOT, 'viewer', 'model.b64.js')
with open(b64p, 'w', encoding='ascii') as f:
    f.write('window.__MODEL_B64="' + b64 + '";\n')

print('EXPORTED %s %d bytes -> %s %d bytes' % (out, len(data), b64p, os.path.getsize(b64p)))
