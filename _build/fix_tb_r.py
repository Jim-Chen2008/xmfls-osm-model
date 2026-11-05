# -*- coding: utf-8 -*-
"""修 GATE_tb_r_-1：负侧高墩外侧实心段原本宽 0（退化面片），
按修复后的 build_scene.py 逻辑重建为 [-18.25, -14.75]，再做全 GATE 镜像审计。"""
import bpy, bmesh, json, os

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
BLEND = os.path.join(ROOT, '_build', 'xmfls_gate.blend')

bpy.ops.wm.open_mainfile(filepath=BLEND)

GATE_C = (281.13, 24.49)
H, OW = 9.4, 13.5
GH_W, TB_W = 5.2, 6.3
u1 = OW / 2.0
u2 = u1 + GH_W          # 11.95
u3 = u2 + TB_W          # 18.25
HOLE = 2.8
HW0, HW1 = -2.20, 1.05
TB_H = 6.0


def uv_box(me, tile):
    uvl = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.y, co.z
            elif ax == 1:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            uvl.data[li].uv = (u / tile, v / tile)


def box(name, x0, x1, y0, y1, z0, z1, mat, collection, uv=4.8):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = False
    if uv:
        uv_box(me, uv)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free(); me.update()
    return ob


def bounds(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return [round(min(xs), 4), round(max(xs), 4)], [round(min(ys), 4), round(max(ys), 4)], [round(min(zs), 4), round(max(zs), 4)]


before = dict(zip(('x', 'y', 'z'), bounds(bpy.data.objects['GATE_tb_r_-1'])))

# ---- 重建负侧实心段：与正侧 [u2+HOLE, u3] 镜像
old = bpy.data.objects['GATE_tb_r_-1']
root = old.parent
C = old.users_collection[0]
mat = old.data.materials[0] if old.data.materials else bpy.data.materials.get('MAT_PANEL')
old_mesh = old.data
bpy.data.objects.remove(old, do_unlink=True)
if old_mesh.users == 0:
    bpy.data.meshes.remove(old_mesh)

r0, r1 = sorted((-u3, -(u2 + HOLE)))          # (-18.25, -14.75)
new = box('GATE_tb_r_-1', r0, r1, HW0, HW1, -0.35, TB_H, mat, C, uv=4.8)
new.parent = root   # 与 build_scene.py 一致：父级逆矩阵保持单位阵，局部坐标即 GATE_ROOT 空间坐标

# ---- 全 GATE 镜像审计
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('GATE_')]
bd = {}
for o in meshes:
    bd[o.name] = bounds(o)[0]

def base_key(n):
    # 末尾 _1 / _-1 视为侧别
    for suf in ('_1', '_-1'):
        if n.endswith(suf):
            return n[:-len(suf)], suf
    return None, None

bad, unpaired = [], []
for n in sorted(bd):
    base, suf = base_key(n)
    if suf != '_1':
        continue
    o = base + '_-1'
    if o not in bd:
        unpaired.append(n)
        continue
    lo, hi = bd[n]
    olo, ohi = bd[o]
    err = round(max(abs(lo + ohi), abs(hi + olo)), 4)
    if err > 0.002:
        bad.append({'base': base, 'pos': [lo, hi], 'neg': [olo, ohi], 'err': err})

report = {
    'tb_r_-1_before': before,
    'tb_r_-1_after': dict(zip(('x', 'y', 'z'), bounds(new))),
    'tb_r_1': dict(zip(('x', 'y', 'z'), bounds(bpy.data.objects['GATE_tb_r_1']))),
    'gate_meshes': len(meshes),
    'asymmetric': bad,
    'unpaired_pos': unpaired,
}

bpy.ops.wm.save_mainfile()
print('HEADLESS ' + json.dumps(report, ensure_ascii=False))
