# -*- coding: utf-8 -*-
"""把 GATE_gh 门卫房墩从 9.4 m 削到横墙底面 5.6 m，压顶（边缘）同步平移下来。
两侧同时处理以保持镜像。"""
import bpy

TOP = 5.6          # 新的顶面世界 z
SIDE = [4, 5, 6, 7, 8, 9, 10, 11]   # 这个盒子的 4 个侧面（法线水平）

for name in ('GATE_gh_1', 'GATE_gh_-1'):
    o = bpy.data.objects[name]
    me = o.data
    zs = [(o.matrix_world @ v.co).z for v in me.vertices]
    z0, z1 = min(zs), max(zs)
    zoff = o.matrix_world.translation.z
    new_local_top = TOP - zoff
    ratio = (TOP - z0) / (z1 - z0)

    uv = me.uv_layers.active.data
    loops = [li for p in me.polygons if p.index in SIDE for li in p.loop_indices]
    vmin = min(uv[li].uv[1] for li in loops)
    for li in loops:
        u, v = uv[li].uv
        uv[li].uv = (u, vmin + (v - vmin) * ratio)

    n_clamped = 0
    for v in me.vertices:
        if v.co.z > new_local_top:
            v.co.z = new_local_top
            n_clamped += 1
    me.update()
    print("{}: z {:.2f}..{:.2f} -> top {:.2f}  uv ratio {:.4f}  clamped {} verts".format(
        name, z0, z1, TOP, ratio, n_clamped))

for name in ('GATE_gh_cap_1', 'GATE_gh_cap_-1'):
    o = bpy.data.objects[name]
    o.location.z += TOP - 9.4
    zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
    print("{}: cap -> z {:.2f}..{:.2f}".format(name, min(zs), max(zs)))

print("done")
