# -*- coding: utf-8 -*-
"""只留 GATE 的平光正立面：修好后 / 删掉 GATE_tb_r_-1（≈修复前）各一张。"""
import bpy, math, os

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, '_build', 'xmfls_gate.blend'))
sc = bpy.context.scene

# 只显示 GATE_* 对象，清掉背后校园体块的干扰
for o in bpy.data.objects:
    if o.type in {'MESH', 'FONT'} and not o.name.startswith('GATE_'):
        o.hide_render = True
    elif o.type in {'LIGHT', 'CAMERA'} and not o.name.startswith('GATE_'):
        o.hide_render = True

sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'SINGLE'
sh.single_color = (0.55, 0.56, 0.58)
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sh.show_shadows = False
sh.show_object_outline = True
sh.object_outline_color = (0.05, 0.05, 0.06)
sc.display.render_aa = '16'
sc.render.resolution_x = 1500
sc.render.resolution_y = 520
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
if not sc.world:
    sc.world = bpy.data.worlds.new('W')
sc.world.use_nodes = False
sc.world.color = (0.985, 0.985, 0.99)

GATE_C = (281.13, 24.49)
ROT = math.radians(-49.6)
NY = (-math.sin(ROT), math.cos(ROT))

cam_data = bpy.data.cameras.new('E')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 46.0
cam = bpy.data.objects.new('E', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
cam.location = (GATE_C[0] + NY[0] * 80, GATE_C[1] + NY[1] * 80, 3.0)
d = (cam.location[0] - GATE_C[0], cam.location[1] - GATE_C[1], 0.0)
cam.rotation_euler = (math.pi / 2, 0.0, math.atan2(d[1], d[0]) + math.pi / 2)

p_after = os.path.join(ROOT, '_shots', 'tbr_iso_after.png')
sc.render.filepath = p_after
bpy.ops.render.render(write_still=True)

bpy.data.objects.remove(bpy.data.objects['GATE_tb_r_-1'], do_unlink=True)
p_before = os.path.join(ROOT, '_shots', 'tbr_iso_before.png')
sc.render.filepath = p_before
bpy.ops.render.render(write_still=True)

print('SHOTS %s | %s' % (p_after, p_before))
