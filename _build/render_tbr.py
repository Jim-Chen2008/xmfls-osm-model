# -*- coding: utf-8 -*-
"""渲染大门正立面（街道侧）与负侧高墩特写。
用法：blender -b -P render_tbr.py -- <after|before> <outprefix>
after  = 用修好的 xmfls_gate.blend
before = 临时把 GATE_tb_r_-1 改回宽 0 的退化面片，复现原始观感
"""
import bpy, bmesh, math, os, sys

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['after', 'tbr_after']
mode = argv[0]
prefix = argv[1]

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, '_build', 'xmfls_gate.blend'))
sc = bpy.context.scene

if mode == 'before':
    ob = bpy.data.objects['GATE_tb_r_-1']
    ob.scale = (0.0, 1.0, 1.0)   # x 方向压成 0 → 复现原退化面片
    bpy.context.view_layer.update()

for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
    try:
        sc.render.engine = eng
        break
    except Exception:
        continue
sc.render.resolution_x = 1600
sc.render.resolution_y = 900
sc.render.film_transparent = False
try:
    sc.eevee.taa_render_samples = 32
except Exception:
    pass
sc.view_settings.view_transform = 'Standard'

GATE_C = (281.13, 24.49)
ROT = math.radians(-49.6)
LX = (math.cos(ROT), math.sin(ROT))        # 大门局部 +x 的世界方向
NY = (-math.sin(ROT), math.cos(ROT))       # 局部 +y = 街道侧法线

cam_data = bpy.data.cameras.new('ELEV')
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('ELEV', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam


def look_at(obj, target):
    d = (obj.location[0] - target[0], obj.location[1] - target[1], obj.location[2] - target[2])
    r = math.hypot(d[0], d[1])
    obj.rotation_euler = (math.atan2(r, -d[2]), 0.0, math.atan2(d[1], d[0]) + math.pi / 2)


shots = []

# 1) 正立面全景
cam_data.ortho_scale = 54.0
cam.location = (GATE_C[0] + NY[0] * 70, GATE_C[1] + NY[1] * 70, 5.2)
look_at(cam, (GATE_C[0], GATE_C[1], 5.2))
p1 = os.path.join(ROOT, '_shots', prefix + '_front.png')
sc.render.filepath = p1
bpy.ops.render.render(write_still=True)
shots.append(p1)

# 2) 负侧高墩特写（局部 x = -16.5 处）
tgt = (GATE_C[0] + LX[0] * (-16.5), GATE_C[1] + LX[1] * (-16.5), 3.0)
cam_data.ortho_scale = 9.5
cam.location = (tgt[0] + NY[0] * 45, tgt[1] + NY[1] * 45, 3.0)
look_at(cam, tgt)
p2 = os.path.join(ROOT, '_shots', prefix + '_negclose.png')
sc.render.filepath = p2
bpy.ops.render.render(write_still=True)
shots.append(p2)

print('SHOTS ' + ' | '.join(shots))
