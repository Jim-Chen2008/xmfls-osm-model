# -*- coding: utf-8 -*-
"""Rebuild only the gate (GATE_* objects) in the current scene, with the two
side openings' sizes swapped: junction hole 2.8 m wide, car gate 2.2 m wide."""
import bpy, bmesh, math
from mathutils import Vector

GATE_C = (281.13, 24.49)
GATE_ROT = math.radians(-49.6)
TEXDIR = r"C:\xmfls test\ds\xmfls-osm-model\_build\tex"


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


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


def make(name, verts, faces, mat, collection, uv=None, recalc=True, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    if uv:
        uv_box(me, uv)
    if recalc:
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free(); me.update()
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat, collection, uv=4.8):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return make(name, v, f, mat, collection, uv=uv)


def bar(name, p0, p1, width, thick, mat, collection):
    (x0, z0), (x1, z1) = p0, p1
    dx, dz = x1 - x0, z1 - z0
    L = math.hypot(dx, dz) or 1e-6
    nx, nz = -dz / L * width / 2, dx / L * width / 2
    y0, y1 = -thick / 2, thick / 2
    v = [(x0 - nx, y0, z0 - nz), (x0 + nx, y0, z0 + nz), (x1 + nx, y0, z1 + nz), (x1 - nx, y0, z1 - nz),
         (x0 - nx, y1, z0 - nz), (x0 + nx, y1, z0 + nz), (x1 + nx, y1, z1 + nz), (x1 - nx, y1, z1 - nz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return make(name, v, f, mat, collection)


def text_mesh(name, body, font_path, size, collection, extrude=0.05, spacing=1.0):
    cu = bpy.data.curves.new(name + '_c', type='FONT')
    cu.body = body
    cu.font = bpy.data.fonts.load(font_path, check_existing=True)
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.extrude = extrude
    cu.resolution_u = 5
    cu.space_character = spacing
    ob = bpy.data.objects.new(name, cu)
    collection.objects.link(ob)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    nob = bpy.data.objects.new(name, me)
    collection.objects.link(nob)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.curves.remove(cu)
    return nob


def main():
    # drop old gate
    for o in list(bpy.data.objects):
        if o.name.startswith('GATE_'):
            bpy.data.objects.remove(o, do_unlink=True)

    panel = bpy.data.materials.get('MAT_PANEL')
    coping = bpy.data.materials.get('MAT_COPING')
    stone = bpy.data.materials.get('MAT_STONE')
    steel = bpy.data.materials.get('MAT_STEEL')
    door = bpy.data.materials.get('MAT_DOOR')
    lawn = bpy.data.materials.get('MAT_LAWN')
    grey = bpy.data.materials.get('MAT_GREY_PAVE') or bpy.data.materials.get('MAT_GREY')
    asphalt = bpy.data.materials.get('MAT_ASPHALT')
    curb = bpy.data.materials.get('MAT_CURB')
    gold = bpy.data.materials.get('MAT_GOLD')
    glass = bpy.data.materials.get('MAT_GLASS')

    C = coll('GATE')
    root = bpy.data.objects.new('GATE_ROOT', None)
    C.objects.link(root)
    root.location = (GATE_C[0], GATE_C[1], 0)
    root.rotation_euler = (0, 0, GATE_ROT)
    objs = []

    def add(o):
        o.parent = root
        objs.append(o)
        return o

    H = 9.4
    OW, OH = 13.5, 5.6
    GH_W, GH_H = 5.2, 9.4
    TB_W, TB_H = 6.3, 6.0
    CG_W, CG_H = 2.2, 2.8       # car side gate (was 2.8)
    EB_W, EB_H = 4.1, 3.6
    HOLE_W = 2.8                # junction hole (was 2.2)
    u1 = OW / 2.0
    u2 = u1 + GH_W
    u3 = u2 + TB_W
    u4 = u3 + CG_W
    u5 = u4 + EB_W
    WY0, WY1 = 0.15, 1.35
    WB = 5.6

    # sign wall + coping
    add(box('GATE_wall', -u2, u2, WY0, WY1, WB, H, panel, C))
    add(box('GATE_wall_coping', -u2 - 0.06, u2 + 0.06, WY0 - 0.08, WY1 + 0.08, H, H + 0.16, coping, C))

    # gold lettering
    chars = '厦门外国语学校'
    pitch = 1.86
    for i, ch in enumerate(chars):
        t = text_mesh('GATE_txt_%d' % i, ch, 'C:/Windows/Fonts/STXINGKA.TTF', 1.70, C, extrude=0.05)
        t.location = ((len(chars) - 1) / 2.0 * pitch - i * pitch, WY1 + 0.02, 7.55)
        t.rotation_euler = (math.radians(90), 0, math.pi)
        t.data.materials.append(gold)
        add(t)
    for w, dx in [('XIAMEN', 4.0), ('FOREIGN', 1.55), ('LANGUAGE', -1.05), ('SCHOOL', -3.55)]:
        t = text_mesh('GATE_en_%s' % w, w, 'C:/Windows/Fonts/calibril.ttf', 0.44, C, extrude=0.03, spacing=1.2)
        t.location = (dx, WY1 + 0.02, 6.62)
        t.rotation_euler = (math.radians(90), 0, math.pi)
        t.data.materials.append(gold)
        add(t)

    for sgn in (-1, 1):
        # 1) inner pier (full height)
        a, b = sorted((sgn * u1, sgn * u2))
        add(box('GATE_gh_%d' % sgn, a, b, -2.90, 1.35, -0.35, GH_H, panel, C))
        add(box('GATE_gh_cap_%d' % sgn, a - 0.06, b + 0.06, -2.98, 1.43, GH_H, GH_H + 0.14, coping, C))
        du = sgn * (u1 + GH_W * 0.5)
        d0, d1 = min(du - 0.55, du + 0.55), max(du - 0.55, du + 0.55)
        add(box('GATE_gh_door_%d' % sgn, d0, d1, -2.96, -2.90, 0.02, 2.30, door, C))
        add(box('GATE_gh_doorframe_%d' % sgn, d0 - 0.10, d1 + 0.10, -2.98, -2.88, 2.30, 2.42, stone, C))
        add(box('GATE_gh_canopy_%d' % sgn, du - 0.95, du + 0.95, -3.40, -2.92, 2.60, 2.72, stone, C))
        for kk in range(3):
            y1 = -2.90 - 0.28 * (kk + 1)
            add(box('GATE_gh_step_%d_%d' % (sgn, kk), du - 1.05, du + 1.05, y1, y1 + 0.28, 0, 0.13 * (3 - kk), stone, C))
        w0, w1 = sorted((du + sgn * 0.95, du + sgn * 1.85))
        add(box('GATE_gh_win_%d' % sgn, w0, w1, -2.94, -2.89, 3.10, 3.55, glass, C))

        # 2) tall pier with junction hole (2.8 x 2.8)
        a, b = sorted((sgn * u2, sgn * u3))
        h0, h1 = sorted((sgn * u2, sgn * (u2 + HOLE_W)))
        HW0, HW1 = -2.20, 1.05
        r0, r1 = sorted((sgn * u3, sgn * (u2 + HOLE_W)))
        add(box('GATE_tb_r_%d' % sgn, r0, r1, HW0, HW1, -0.35, TB_H, panel, C))
        add(box('GATE_tb_top_%d' % sgn, h0, h1, HW0, HW1, 2.95, TB_H, panel, C))
        add(box('GATE_tb_sill_%d' % sgn, h0, h1, HW0, HW1, -0.35, 0.15, panel, C))
        add(box('GATE_tb_cap_%d' % sgn, a - 0.06, b + 0.06, -2.28, 1.12, TB_H, TB_H + 0.14, coping, C))
        add(box('GATE_tb_gate_top_%d' % sgn, h0 + 0.06, h1 - 0.06, -0.48, -0.42, 1.40, 1.46, steel, C))
        add(box('GATE_tb_gate_bot_%d' % sgn, h0 + 0.06, h1 - 0.06, -0.48, -0.42, 0.16, 0.22, steel, C))
        xx = h0 + 0.18
        gk = 0
        while xx < h1 - 0.22:
            add(bar('GATE_tb_gx1_%d_%d' % (sgn, gk), (xx, 0.16), (xx + 0.46, 1.42), 0.032, 0.032, steel, C))
            add(bar('GATE_tb_gx2_%d_%d' % (sgn, gk), (xx + 0.46, 0.16), (xx, 1.42), 0.032, 0.032, steel, C))
            xx += 0.46
            gk += 1

        # 3) car side gate (2.2 wide)
        g0, g1 = sorted((sgn * u3, sgn * u4))
        add(box('GATE_cg_lintel_%d' % sgn, g0, g1, -1.60, 0.35, CG_H, TB_H, panel, C))
        add(box('GATE_cg_top_%d' % sgn, g0 + 0.05, g1 - 0.05, -0.02, 0.04, 1.45, 1.51, steel, C))
        add(box('GATE_cg_bot_%d' % sgn, g0 + 0.05, g1 - 0.05, -0.02, 0.04, 0.06, 0.12, steel, C))
        x = g0 + 0.12
        k = 0
        while x < g1 - 0.2:
            add(bar('GATE_cg_x1_%d_%d' % (sgn, k), (x, 0.06), (x + 0.4, 1.48), 0.035, 0.035, steel, C))
            add(bar('GATE_cg_x2_%d_%d' % (sgn, k), (x + 0.4, 0.06), (x, 1.48), 0.035, 0.035, steel, C))
            x += 0.4
            k += 1

        # 4) end pier
        a, b = sorted((sgn * u4, sgn * u5))
        add(box('GATE_eb_%d' % sgn, a, b, -1.60, 0.75, -0.35, EB_H, panel, C))
        add(box('GATE_eb_cap_%d' % sgn, a - 0.06, b + 0.06, -1.68, 0.82, EB_H, EB_H + 0.14, coping, C))
        o0, o1 = sorted((sgn * (u4 + 0.7), sgn * (u4 + 2.4)))
        add(box('GATE_eb_door_%d' % sgn, o0, o1, -1.66, -1.60, 0.02, 2.40, door, C))

    # central retractable gate
    add(box('GATE_mg_top', -u1 + 0.1, u1 - 0.1, -0.02, 0.04, 1.42, 1.48, steel, C))
    add(box('GATE_mg_bot', -u1 + 0.1, u1 - 0.1, -0.02, 0.04, 0.06, 0.12, steel, C))
    x = -u1 + 0.2
    k = 0
    while x < u1 - 0.3:
        add(bar('GATE_mg_x1_%d' % k, (x, 0.06), (x + 0.55, 1.44), 0.032, 0.032, steel, C))
        add(bar('GATE_mg_x2_%d' % k, (x + 0.55, 0.06), (x, 1.44), 0.032, 0.032, steel, C))
        x += 0.55
        k += 1

    # street side ground
    add(box('GATE_street_lawn', -36, 36, 1.9, 5.0, 0, 0.07, lawn, C, uv=3.0))
    add(box('GATE_street_walk', -36, 36, 5.0, 7.6, 0, 0.10, grey, C, uv=2.0))
    add(box('GATE_street_road', -36, 36, 7.6, 17.0, 0, 0.05, asphalt, C, uv=6.0))
    add(box('GATE_road_curb', -36, 36, 7.4, 7.65, 0, 0.14, curb, C, uv=2.0))

    print('gate rebuilt', len(objs))


if __name__ == '__main__':
    main()
