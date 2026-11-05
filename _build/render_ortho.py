# -*- coding: utf-8 -*-
"""正射俯视渲染广场区域，与航拍截图同框对照。渲染后垂直翻转，使 image x=世界+x、image y向下=世界+y。"""
import bpy, os, math

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, '_build', 'xmfls_gate.blend'))

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1337
sc.render.resolution_y = 1263
sc.view_settings.view_transform = 'Standard'

cam_data = bpy.data.cameras.new('ORTHO')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 1337 / 13.94  # 95.9 m 水平视野
cam = bpy.data.objects.new('ORTHO', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

cx = 244.32 + (668.5 - 382) / 13.94   # 264.87
cy = -8.92 + (631.5 - 272) / 13.94    # 16.87
cam.location = (cx, cy, 120.0)
cam.rotation_euler = (0, 0, 0)  # 俯视；Blender 图像 y 向上 = 世界 +y（事后翻转）

out = os.path.join(ROOT, '_shots', 'plaza_ortho.png')
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('RENDERED', out)
