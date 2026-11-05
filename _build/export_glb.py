# -*- coding: utf-8 -*-
"""把 xmfls_gate.blend 导出为 viewer/gate_campus.glb（贴图打包）。"""
import bpy, os

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
src = os.path.join(ROOT, '_build', 'xmfls_gate.blend')
out = os.path.join(ROOT, 'viewer', 'gate_campus.glb')

bpy.ops.wm.open_mainfile(filepath=src)
# 打包全部贴图，确保 GLB 自包含
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
print('EXPORTED', out, os.path.getsize(out))
