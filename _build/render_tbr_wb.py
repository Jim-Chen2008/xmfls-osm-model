# -*- coding: utf-8 -*-
"""Workbench 平光正立面 + 负侧高墩特写（几何判读用）。
用法：blender -b -P render_tbr_wb.py -- <after|before> <outprefix>
"""
import bpy, math, os, sys

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['after', 'tbr_wb_after']
mode, prefix = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, '_build', 'xmfls_gate.blend'))
sc = bpy.context.scene

if mode == 'before':
    bpy.data.objects['GATE_tb_r_-1'].scale = (0.0, 1.0, 1.0)
    bpy.context.view_layer.update()

sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'SINGLE'
sh.single_color = (0.62, 0.62, 0.64)
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sh.curvature_ridge_factor = 1.0
sh.curvature_valley_factor = 1.0
sh.show_shadows = False
sh.show_object_outline = True
sh.object_outline_color = (0.1, 0.1, 0.12)
sc.display.render_aa = '16'
sc.render.resolution_x = 1800
sc.render.resolution_y = 760
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
sc.world.color = (0.93, 0.93, 0.94)

GATE_C = (281.13, 24.49)
ROT = math.radians(-49.6)
LX = (math.cos(ROT), math.sin(ROT))
NY = (-math.sin(ROT), math.cos(ROT))

cam_data = bpy.data.cameras.new('ELEV')
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('ELEV', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam


def look_at(obj, t):
    d = (obj.location[0] - t[0], obj.location[1] - t[1], obj.location[2] - t[2])
    r = math.hypot(d[0], d[1])
    obj.rotation_euler = (math.atan2(r, -d[2]), 0.0, math.atan2(d[1], d[0]) + math.pi / 2)


cam_data.ortho_scale = 53.0
cam.location = (GATE_C[0] + NY[0] * 70, GATE_C[1] + NY[1] * 70, 4.8)
look_at(cam, (GATE_C[0], GATE_C[1], 4.8))
p1 = os.path.join(ROOT, '_shots', prefix + '_front.png')
sc.render.filepath = p1
bpy.ops.render.render(write_still=True)

# 负侧高墩特写：局部 x -21.05..-11.95 一段
tgt = (GATE_C[0] + LX[0] * (-16.5), GATE_C[1] + LX[1] * (-16.5), 3.2)
cam_data.ortho_scale = 11.5
cam.location = (tgt[0] + NY[0] * 45, tgt[1] + NY[1] * 45, 3.2)
look_at(cam, tgt)
p2 = os.path.join(ROOT, '_shots', prefix + '_negclose.png')
sc.render.filepath = p2
bpy.ops.render.render(write_still=True)

# 正侧同段，做对照
tgt2 = (GATE_C[0] + LX[0] * (16.5), GATE_C[1] + LX[1] * (16.5), 3.2)
cam.location = (tgt2[0] + NY[0] * 45, tgt2[1] + NY[1] * 45, 3.2)
look_at(cam, tgt2)
p3 = os.path.join(ROOT, '_shots', prefix + '_posclose.png')
sc.render.filepath = p3
bpy.ops.render.render(write_still=True)

print('SHOTS ' + ' | '.join([p1, p2, p3]))
