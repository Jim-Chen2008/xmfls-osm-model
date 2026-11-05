# -*- coding: utf-8 -*-
"""
鍘﹂棬澶栧浗璇鏍★紙娴锋钵鏍″尯锛夆€斺€?澶ч棬 + 鍠锋硥鑺卞渻  (v3, 渚濇嵁 2026 鏂扮収鐗?
鍗曚綅锛氱背銆備笘鐣屽潗鏍囨部鐢ㄦ牎鍥?GLB锛坸 涓溿€亂 鍖椼€亃 涓婏級銆?
澶ч棬涓績 (281.13, 24.49)锛屽闈㈣蛋鍚?(0.649,-0.762)锛屽渚?琛楅亾)娉曠嚎 (0.762,0.649)銆?
鍠锋硥涓績 (244.32, -8.92)銆?
"""
import bpy, bmesh, math, random, os
from mathutils import Vector

ROOT = r"C:\xmfls test\ds\xmfls-osm-model"
CAMPUS = r"C:\Users\Jim\Downloads\鍘﹂棬澶栧浗璇鏍★紙娴锋钵鏍″尯锛?edited-20261027-1632-edited-20261027-1659.glb"
TEX = os.path.join(ROOT, "_build", "tex")

GATE_C = (281.13, 24.49)
GATE_ROT = math.radians(-49.6)
FOUNTAIN_C = (244.32, -8.92)

# ---------------------------------------------------------------- 鍩虹

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def img_mat(name, img_path, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    img = bpy.data.images.load(img_path, check_existing=True)
    try:
        img.pack()
    except Exception:
        pass
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Smart'
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    return m


def flat_mat(name, color, rough=0.8, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


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


def make(name, verts, faces, mat, collection, smooth=False, uv=None, recalc=True):
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


def cyl(name, r, z0, z1, mat, collection, cx=0, cy=0, seg=32, r_top=None, smooth=True, uv=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=(r if r_top is None else r_top), depth=abs(z1 - z0))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, cy, (z0 + z1) / 2.0))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); collection.objects.link(ob)
    if mat: me.materials.append(mat)
    for p in me.polygons: p.use_smooth = smooth
    if uv: uv_box(me, uv)
    return ob


def band_solid(name, sections, z0, z1, mat, collection, uv=4.8, caps=True):
    """sections: [(xin,yin,xout,yout), ...] 娌胯矾寰勩€?""
    verts, faces = [], []
    n = len(sections)
    for xi, yi, xo, yo in sections:
        verts += [(xi, yi, z0), (xo, yo, z0), (xo, yo, z1), (xi, yi, z1)]
    for i in range(n - 1):
        b, c = i * 4, (i + 1) * 4
        faces += [(b, c, c + 1, b + 1), (b + 3, b + 2, c + 2, c + 3),
                  (b, b + 3, c + 3, c), (b + 1, c + 1, c + 2, b + 2)]
    if caps:
        faces += [(0, 1, 2, 3), ((n - 1) * 4 + 3, (n - 1) * 4 + 2, (n - 1) * 4 + 1, (n - 1) * 4)]
    return make(name, verts, faces, mat, collection, uv=uv)


def arc_solid(name, cx, cy, r0, r1, a0, a1, z0, z1, mat, collection, seg=64, uv=4.8, caps=True):
    sections = []
    for i in range(seg + 1):
        a = a0 + (a1 - a0) * i / seg
        sections.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a),
                         cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    return band_solid(name, sections, z0, z1, mat, collection, uv, caps)


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


def smooth_subdiv(ob, levels=1):
    md = ob.modifiers.new('sub', 'SUBSURF')
    md.levels = levels
    md.render_levels = levels
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.remove(md)
    old = ob.data
    ob.data = me2
    for p in me2.polygons:
        p.use_smooth = True
    bpy.data.meshes.remove(old)


def text_mesh(name, body, font_path, size, collection, extrude=0.045, spacing=1.0):
    cu = bpy.data.curves.new(name + '_c', type='FONT')
    cu.body = body
    try:
        cu.font = bpy.data.fonts.load(font_path, check_existing=True)
    except Exception as e:
        print('FONT FAIL', font_path, e)
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


def make_tree(name, x, y, trunk_h, canopy, seed, C, M, subdiv=3, sub=1, trunk_r=0.28):
    cyl(name + '_trunk', trunk_r, 0, trunk_h, M['trunk'], C, cx=x, cy=y, seg=12, r_top=trunk_r * 0.68, uv=1.0)
    rnd = random.Random(seed)
    blobs = [(0, 0, trunk_h + canopy[2] * 0.62, canopy[0], canopy[1], canopy[2]),
             (-canopy[0] * 0.50, canopy[1] * 0.18, trunk_h + canopy[2] * 0.42, canopy[0] * 0.72, canopy[1] * 0.78, canopy[2] * 0.72),
             (canopy[0] * 0.46, -canopy[1] * 0.22, trunk_h + canopy[2] * 0.50, canopy[0] * 0.68, canopy[1] * 0.72, canopy[2] * 0.68),
             (canopy[0] * 0.10, canopy[1] * 0.45, trunk_h + canopy[2] * 0.75, canopy[0] * 0.60, canopy[1] * 0.58, canopy[2] * 0.55)]
    for bi, (ox, oy, oz, sx, sy, sz) in enumerate(blobs):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
        for v in bm.verts:
            v.co *= 0.80 + 0.36 * rnd.random()
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(x + ox, y + oy, oz), verts=bm.verts)
        me = bpy.data.meshes.new(name + '_can%d' % bi)
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name + '_can%d' % bi, me)
        C.objects.link(ob)
        me.materials.append(M['leaf'] if bi % 2 == 0 else M['leaf2'])
        smooth_subdiv(ob, sub)


def make_shrub(name, x, y, r, z0, C, M, mat=None, squash=1.15, seed=0):
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        v.co *= 0.74 + 0.42 * rnd.random()
    bmesh.ops.scale(bm, vec=(r, r, r * squash), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(x, y, z0 + r * squash * 0.85), verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); C.objects.link(ob)
    me.materials.append(mat or M['hedge2'])
    smooth_subdiv(ob, 1)


# ---------------------------------------------------------------- 鏉愯川

def build_materials():
    M = {}
    M['panel'] = img_mat('MAT_PANEL', os.path.join(TEX, 'panel_white.png'), rough=0.55)
    M['concrete'] = img_mat('MAT_CONCRETE', os.path.join(TEX, 'concrete.png'), rough=0.85)
    M['brick'] = img_mat('MAT_BRICK', os.path.join(TEX, 'brick.png'), rough=0.9)
    M['paving'] = img_mat('MAT_PAVING', os.path.join(TEX, 'paving.png'), rough=0.85)
    M['plaza'] = img_mat('MAT_PLAZA', os.path.join(TEX, 'plaza.png'), rough=0.9)
    M['stone'] = flat_mat('MAT_STONE', (0.60, 0.585, 0.55), rough=0.82)
    M['stone_dark'] = flat_mat('MAT_STONE_DARK', (0.42, 0.415, 0.40), rough=0.8)
    M['coping'] = flat_mat('MAT_COPING', (0.80, 0.80, 0.78), rough=0.6)
    M['gold'] = flat_mat('MAT_GOLD', (0.88, 0.68, 0.30), rough=0.32, metal=0.6)
    M['steel'] = flat_mat('MAT_STEEL', (0.55, 0.57, 0.59), rough=0.38, metal=0.8)
    M['darksteel'] = flat_mat('MAT_DARKSTEEL', (0.12, 0.125, 0.13), rough=0.45, metal=0.5)
    M['door'] = flat_mat('MAT_DOOR', (0.17, 0.18, 0.185), rough=0.4, metal=0.2)
    M['glass'] = flat_mat('MAT_GLASS', (0.18, 0.25, 0.27), rough=0.12, metal=0.4)
    M['red'] = flat_mat('MAT_RED', (0.55, 0.055, 0.05), rough=0.6)
    M['red_tent'] = flat_mat('MAT_RED_TENT', (0.62, 0.07, 0.06), rough=0.7)
    M['white'] = flat_mat('MAT_WHITE', (0.86, 0.86, 0.83), rough=0.65)
    M['water'] = flat_mat('MAT_WATER', (0.07, 0.13, 0.13), rough=0.18)
    M['water_dark'] = flat_mat('MAT_WATER_DARK', (0.05, 0.10, 0.10), rough=0.16)
    M['basin'] = flat_mat('MAT_BASIN', (0.40, 0.435, 0.41), rough=0.75)
    M['lawn'] = flat_mat('MAT_LAWN', (0.26, 0.38, 0.135), rough=1.0)
    M['groundcover'] = flat_mat('MAT_GC', (0.15, 0.22, 0.085), rough=1.0)
    M['hedge'] = flat_mat('MAT_HEDGE', (0.12, 0.23, 0.075), rough=1.0)
    M['hedge2'] = flat_mat('MAT_HEDGE2', (0.16, 0.29, 0.095), rough=1.0)
    M['leaf'] = flat_mat('MAT_LEAF', (0.085, 0.175, 0.06), rough=1.0)
    M['leaf2'] = flat_mat('MAT_LEAF2', (0.125, 0.235, 0.075), rough=1.0)
    M['trunk'] = flat_mat('MAT_TRUNK', (0.22, 0.185, 0.15), rough=0.95)
    M['soil'] = flat_mat('MAT_SOIL', (0.20, 0.155, 0.11), rough=1.0)
    M['asphalt'] = flat_mat('MAT_ASPHALT', (0.245, 0.25, 0.25), rough=0.92)
    M['curb'] = flat_mat('MAT_CURB', (0.66, 0.645, 0.615), rough=0.8)
    M['grey'] = flat_mat('MAT_GREY_PAVE', (0.685, 0.675, 0.655), rough=0.9)
    return M


# ---------------------------------------------------------------- 澶ч棬

def build_gate(M):
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
    OW = 13.5                         # 涓ぎ闂ㄦ礊
    GH_W, GH_H = 5.2, 9.4             # 闂ㄥ崼鎴垮ⅸ = 閫氶珮澧欏ⅸ锛堟暣鏍硅惤鍦帮級
    TB_W, TB_H = 6.3, 6.0             # 楂樺ⅸ
    CG_W, CG_H = 2.2, 2.8             # 姹借溅渚ч棬锛堟渶澶栦晶锛屾礊鍙ｆ洿浣庯級
    EB_W, EB_H = 4.1, 3.6             # 绔ⅸ
    u1 = OW / 2.0                     # 6.75
    u2 = u1 + GH_W                    # 11.95
    u3 = u2 + TB_W                    # 18.25
    u4 = u3 + CG_W                    # 21.05
    u5 = u4 + EB_W                    # 25.15
    WY0, WY1 = 0.15, 1.35
    WB = 5.6                          # 楂樺搴曟爣楂?

    # ---------- 妯锛堣法涓ぎ闂ㄦ礊 + 涓や晶闂ㄥ崼鎴匡級
    add(box('GATE_wall', -u2, u2, WY0, WY1, WB, H, M['panel'], C, uv=4.8))
    add(box('GATE_wall_coping', -u2 - 0.06, u2 + 0.06, WY0 - 0.08, WY1 + 0.08, H, H + 0.16, M['coping'], C))

    # ---------- 閲戣壊瀛?
    chars = '鍘﹂棬澶栧浗璇鏍?
    pitch = 1.86
    for i, ch in enumerate(chars):
        t = text_mesh('GATE_txt_%d' % i, ch, 'C:/Windows/Fonts/STXINGKA.TTF', 1.70, C, extrude=0.05)
        t.location = ((len(chars) - 1) / 2.0 * pitch - i * pitch, WY1 + 0.02, 7.55)
        t.rotation_euler = (math.radians(90), 0, math.pi)
        t.data.materials.append(M['gold'])
        add(t)
    for w, dx in [('XIAMEN', 4.0), ('FOREIGN', 1.55), ('LANGUAGE', -1.05), ('SCHOOL', -3.55)]:
        t = text_mesh('GATE_en_%s' % w, w, 'C:/Windows/Fonts/calibril.ttf', 0.44, C, extrude=0.03, spacing=1.2)
        t.location = (dx, WY1 + 0.02, 6.62)
        t.rotation_euler = (math.radians(90), 0, math.pi)
        t.data.materials.append(M['gold'])
        add(t)

    # ---------- 涓や晶闂ㄥⅸ缁?
    for sgn in (-1, 1):
        # 1) 闂ㄥ崼鎴垮ⅸ锛堥€氶珮銆佷笌妯鍚屾繁锛岃繛鎴愭暣鍧楋級
        a, b = sorted((sgn * u1, sgn * u2))
        add(box('GATE_gh_%d' % sgn, a, b, -2.90, 1.35, -0.35, GH_H, M['panel'], C, uv=4.8))
        add(box('GATE_gh_cap_%d' % sgn, a - 0.06, b + 0.06, -2.98, 0.42, GH_H, GH_H + 0.14, M['coping'], C))
        du = sgn * (u1 + GH_W * 0.5)
        d0, d1 = min(du - 0.55, du + 0.55), max(du - 0.55, du + 0.55)
        add(box('GATE_gh_door_%d' % sgn, d0, d1, -2.96, -2.90, 0.02, 2.30, M['door'], C))
        add(box('GATE_gh_doorframe_%d' % sgn, d0 - 0.10, d1 + 0.10, -2.98, -2.88, 2.30, 2.42, M['stone'], C))
        add(box('GATE_gh_canopy_%d' % sgn, du - 0.95, du + 0.95, -3.40, -2.92, 2.60, 2.72, M['stone'], C))
        for kk in range(3):
            y1 = -2.90 - 0.28 * (kk + 1)
            add(box('GATE_gh_step_%d_%d' % (sgn, kk), du - 1.05, du + 1.05, y1, y1 + 0.28, 0, 0.13 * (3 - kk), M['stone'], C))
        w0, w1 = sorted((du + sgn * 0.95, du + sgn * 1.85))
        add(box('GATE_gh_win_%d' % sgn, w0, w1, -2.94, -2.89, 3.10, 3.55, M['glass'], C))
        # 鎽勫儚鏈猴紙楂樺涓嬫部锛?
        cx0, cx1 = sgn * (u1 + 0.20), sgn * (u1 + 0.55)
        add(box('GATE_cam_%d' % sgn, min(cx0, cx1), max(cx0, cx1), -2.98, -2.90, 4.75, 4.88, M['white'], C))

        # 2) 楂樺ⅸ锛氬湪鈥滃唴澧?| 楂樺ⅸ鈥濅氦鐣屽鎸?2.2 脳 2.8 m 閫氭礊锛堝唴瑁呬几缂╅棬锛?
        a, b = sorted((sgn * u2, sgn * u3))
        h0, h1 = sorted((sgn * u2, sgn * (u2 + 2.8)))
        HW0, HW1 = -2.20, 1.05
        r0, r1 = sorted((sgn * u3, sgn * (u2 + 2.8)))
        add(box('GATE_tb_r_%d' % sgn, r0, r1, HW0, HW1, -0.35, TB_H, M['panel'], C, uv=4.8))
        add(box('GATE_tb_top_%d' % sgn, h0, h1, HW0, HW1, 2.95, TB_H, M['panel'], C, uv=4.8))
        add(box('GATE_tb_sill_%d' % sgn, h0, h1, HW0, HW1, -0.35, 0.15, M['panel'], C, uv=4.8))
        add(box('GATE_tb_cap_%d' % sgn, a - 0.06, b + 0.06, -2.28, 1.12, TB_H, TB_H + 0.14, M['coping'], C))
        # 娲炲唴浼哥缉闂細涓嬮儴 1.4 m锛屼笂閮ㄧ暀绌?
        add(box('GATE_tb_gate_top_%d' % sgn, h0 + 0.06, h1 - 0.06, -0.48, -0.42, 1.40, 1.46, M['steel'], C))
        add(box('GATE_tb_gate_bot_%d' % sgn, h0 + 0.06, h1 - 0.06, -0.48, -0.42, 0.16, 0.22, M['steel'], C))
        xx = h0 + 0.18
        gk = 0
        while xx < h1 - 0.22:
            add(bar('GATE_tb_gx1_%d_%d' % (sgn, gk), (xx, 0.16), (xx + 0.46, 1.42), 0.032, 0.032, M['steel'], C))
            add(bar('GATE_tb_gx2_%d_%d' % (sgn, gk), (xx + 0.46, 0.16), (xx, 1.42), 0.032, 0.032, M['steel'], C))
            xx += 0.46
            gk += 1

        # 3) 姹借溅渚ч棬
        g0, g1 = sorted((sgn * u3, sgn * u4))
        add(box('GATE_cg_lintel_%d' % sgn, g0, g1, -1.60, 0.35, CG_H, TB_H, M['panel'], C, uv=4.8))
        add(box('GATE_cg_top_%d' % sgn, g0 + 0.05, g1 - 0.05, -0.02, 0.04, 1.45, 1.51, M['steel'], C))
        add(box('GATE_cg_bot_%d' % sgn, g0 + 0.05, g1 - 0.05, -0.02, 0.04, 0.06, 0.12, M['steel'], C))
        x = g0 + 0.12
        k = 0
        while x < g1 - 0.2:
            add(bar('GATE_cg_x1_%d_%d' % (sgn, k), (x, 0.06), (x + 0.4, 1.48), 0.035, 0.035, M['steel'], C))
            add(bar('GATE_cg_x2_%d_%d' % (sgn, k), (x + 0.4, 0.06), (x, 1.48), 0.035, 0.035, M['steel'], C))
            x += 0.4
            k += 1

        # 4) 绔ⅸ
        a, b = sorted((sgn * u4, sgn * u5))
        add(box('GATE_eb_%d' % sgn, a, b, -1.60, 0.75, -0.35, EB_H, M['panel'], C, uv=4.8))
        add(box('GATE_eb_cap_%d' % sgn, a - 0.06, b + 0.06, -1.68, 0.82, EB_H, EB_H + 0.14, M['coping'], C))
        o0, o1 = sorted((sgn * (u4 + 0.7), sgn * (u4 + 2.4)))
        add(box('GATE_eb_door_%d' % sgn, o0, o1, -1.66, -1.60, 0.02, 2.40, M['door'], C))

    # ---------- 涓ぎ鎺ㄦ媺闂?
    add(box('GATE_mg_top', -u1 + 0.1, u1 - 0.1, -0.02, 0.04, 1.42, 1.48, M['steel'], C))
    add(box('GATE_mg_bot', -u1 + 0.1, u1 - 0.1, -0.02, 0.04, 0.06, 0.12, M['steel'], C))
    x = -u1 + 0.2
    k = 0
    while x < u1 - 0.3:
        add(bar('GATE_mg_x1_%d' % k, (x, 0.06), (x + 0.55, 1.44), 0.032, 0.032, M['steel'], C))
        add(bar('GATE_mg_x2_%d' % k, (x + 0.55, 0.06), (x, 1.44), 0.032, 0.032, M['steel'], C))
        x += 0.55
        k += 1

    # ---------- 琛楅亾渚?/ 鏍″唴鍦伴潰
    add(box('GATE_street_lawn', -36, 36, 1.9, 5.0, 0, 0.07, M['lawn'], C, uv=3.0))
    add(box('GATE_street_walk', -36, 36, 5.0, 7.6, 0, 0.10, M['grey'], C, uv=2.0))
    add(box('GATE_street_road', -36, 36, 7.6, 17.0, 0, 0.05, M['asphalt'], C, uv=6.0))
    add(box('GATE_road_curb', -36, 36, 7.4, 7.65, 0, 0.14, M['curb'], C, uv=2.0))

    print('gate objects', len(objs))
    return root, objs


# ---------------------------------------------------------------- 鍠锋硥

def build_fountain(M):
    C = coll('FOUNTAIN')
    cx, cy = FOUNTAIN_C
    R_OUT, R_RIM, R_DRUM = 8.7, 8.0, 3.55
    Z_WATER = 0.30

    # 鍠锋硥澶栧湀鐭抽摵瑁咃紙绐勭幆锛?
    arc_solid('FNT_apron', cx, cy, R_OUT, 10.4, 0, 2 * math.pi, 0, 0.07, M['grey'], C, seg=96, uv=3.0, caps=False)
    arc_solid('FNT_apron_edge', cx, cy, 10.2, 10.4, 0, 2 * math.pi, 0, 0.09, M['curb'], C, seg=96, uv=2.0, caps=False)

    # 澶栧湀鍧愬嚦寮忔睜澹?
    arc_solid('FNT_curb', cx, cy, R_RIM, R_OUT, 0, 2 * math.pi, 0, 0.40, M['stone'], C, seg=96, uv=2.0, caps=False)
    arc_solid('FNT_curb_cap', cx, cy, R_RIM - 0.05, R_OUT + 0.04, 0, 2 * math.pi, 0.40, 0.46, M['curb'], C, seg=96, uv=2.0, caps=False)

    # 姹犲簳
    verts, faces = [], []
    seg = 96
    prof = [(R_RIM, 0.34), (7.0, 0.30), (5.2, 0.27), (R_DRUM + 0.1, 0.24)]
    for k in range(len(prof) - 1):
        r0, z0 = prof[k]
        r1, z1 = prof[k + 1]
        base = len(verts)
        for i in range(seg + 1):
            a = 2 * math.pi * i / seg
            verts.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0))
            verts.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a), z1))
        for i in range(seg):
            b = base + i * 2
            faces.append((b, b + 2, b + 3, b + 1))
    make('FNT_floor', verts, faces, M['basin'], C, recalc=False)

    arc_solid('FNT_water', cx, cy, 3.90, R_RIM - 0.05, 0, 2 * math.pi, Z_WATER, Z_WATER + 0.02,
              M['water'], C, seg=96, uv=2.0, caps=False)
    # 涓ぎ涓ょ骇榧撳骇
    cyl('FNT_drum_base', 5.1, 0.16, 0.30, M['basin'], C, cx=cx, cy=cy, seg=64, uv=2.0)
    cyl('FNT_drum', R_DRUM, 0.38, 0.98, M['brick'], C, cx=cx, cy=cy, seg=64, uv=1.2)
    arc_solid('FNT_drum_cap', cx, cy, R_DRUM, R_DRUM + 0.22, 0, 2 * math.pi, 0.98, 1.10, M['stone'], C, seg=64, uv=2.0, caps=False)
    cyl('FNT_drum_water', R_DRUM - 0.04, 1.04, 1.055, M['water_dark'], C, cx=cx, cy=cy, seg=64)
    cyl('FNT_nozzle', 0.15, 1.05, 1.36, M['steel'], C, cx=cx, cy=cy, seg=16)
    cyl('FNT_nozzle2', 0.06, 1.35, 1.54, M['steel'], C, cx=cx, cy=cy, seg=12)
    print('fountain ok')


# ---------------------------------------------------------------- 鑺卞渻

def bed_sections(n=72, a0=math.radians(-95), a1=math.radians(-18)):
    """鑺卞渻寮э細鍠锋硥鍖椻€旇タ鍖椾晶锛岃创妞渾澶栫紭锛堣埅鎷嶅疄鏅姳鍦冨湪骞垮満杈圭晫澶栵級銆?""
    cx, cy = FOUNTAIN_C
    secs = []
    for i in range(n + 1):
        t = i / n
        a = a0 + (a1 - a0) * t
        w = 2.8 + 5.6 * (math.sin(math.pi * t) ** 0.7)
        rin = 9.9 + 0.30 * math.sin(math.pi * t)
        rout = rin + w
        secs.append((a, rin, rout, t))
    return secs


def build_bed(M):
    C = coll('BED')
    cx, cy = FOUNTAIN_C
    secs = bed_sections()
    Z_TOP = 0.40

    rin_pts = [(cx + ri * math.cos(a), cy + ri * math.sin(a)) for a, ri, ro, t in secs]
    rout_pts = [(cx + ro * math.cos(a), cy + ro * math.sin(a)) for a, ri, ro, t in secs]

    # 渚х煶锛堝唴銆佸锛?
    band_solid('BED_kerb_in', [(i[0], i[1], i[0] + 0.30 * math.cos(a), i[1] + 0.30 * math.sin(a))
                               for (a, ri, ro, t), i in zip(secs, rin_pts)], 0, Z_TOP, M['curb'], C, uv=2.0)
    band_solid('BED_kerb_out', [(o[0] - 0.30 * math.cos(a), o[1] - 0.30 * math.sin(a), o[0], o[1])
                                for (a, ri, ro, t), o in zip(secs, rout_pts)], 0, Z_TOP, M['curb'], C, uv=2.0)
    # 绉嶆鍦?+ 鍦拌
    band_solid('BED_soil', [(i[0] + 0.25 * math.cos(a), i[1] + 0.25 * math.sin(a),
                             o[0] - 0.25 * math.cos(a), o[1] - 0.25 * math.sin(a))
                            for (a, ri, ro, t), i, o in zip(secs, rin_pts, rout_pts)], 0, Z_TOP - 0.04, M['soil'], C, uv=2.0)
    band_solid('BED_gc', [(i[0] + 0.28 * math.cos(a), i[1] + 0.28 * math.sin(a),
                           o[0] - 0.28 * math.cos(a), o[1] - 0.28 * math.sin(a))
                          for (a, ri, ro, t), i, o in zip(secs, rin_pts, rout_pts)], Z_TOP - 0.04, Z_TOP, M['groundcover'], C, uv=1.5)

    # 鐞冨舰鐏屾湪涓涳紙涓绘櫙锛屽瘑妞嶏級
    rnd = random.Random(21)
    shrub_specs = []
    for i in range(46):
        deg = -92 + 72 * (i / 45.0)
        frac = 0.16 + 0.66 * rnd.random()
        r = 0.42 + 0.52 * rnd.random()
        shrub_specs.append((deg, frac, r))
    # 灏戦噺澶х亴鏈?
    for deg, frac, r in [(-85, 0.55, 0.95), (-70, 0.45, 1.00), (-55, 0.62, 1.05), (-40, 0.40, 0.95), (-25, 0.55, 0.85)]:
        shrub_specs.append((deg, frac, r))

    for i, (deg, frac, r) in enumerate(shrub_specs):
        a = math.radians(deg)
        t = (a - secs[0][0]) / (secs[-1][0] - secs[0][0])
        t = max(0.0, min(1.0, t))
        idx = t * (len(secs) - 1)
        i0 = int(idx); i1 = min(i0 + 1, len(secs) - 1)
        f = idx - i0
        r_in = secs[i0][1] * (1 - f) + secs[i1][1] * f
        r_out = secs[i0][2] * (1 - f) + secs[i1][2] * f
        rr = r_in + (r_out - r_in) * frac
        x = cx + rr * math.cos(a)
        y = cy + rr * math.sin(a)
        make_shrub('BED_shrub%02d' % i, x, y, r, Z_TOP, C, M, M['hedge2'] if i % 3 else M['hedge'], 1.10, i)

    # 灏忎箶鏈紙3 鏍級
    for i, (deg, frac, th, cw) in enumerate([(-82, 0.55, 2.2, (1.7, 1.6, 1.5)),
                                             (-58, 0.62, 2.6, (2.3, 2.1, 2.0)),
                                             (-30, 0.55, 2.3, (1.9, 1.8, 1.7))]):
        a = math.radians(deg)
        t = (a - secs[0][0]) / (secs[-1][0] - secs[0][0])
        idx = t * (len(secs) - 1)
        i0 = int(idx); i1 = min(i0 + 1, len(secs) - 1)
        f = idx - i0
        r_in = secs[i0][1] * (1 - f) + secs[i1][1] * f
        r_out = secs[i0][2] * (1 - f) + secs[i1][2] * f
        rr = r_in + (r_out - r_in) * frac
        x = cx + rr * math.cos(a)
        y = cy + rr * math.sin(a)
        make_tree('BED_tree%d' % i, x, y, th, cw, 30 + i, C, M, subdiv=2, sub=1, trunk_r=0.16)

    # 澶ф鏍戯紙鑺卞渻瑗跨锛?
    a = math.radians(-90)
    x = cx + 14.2 * math.cos(a)
    y = cy + 14.2 * math.sin(a)
    make_tree('BED_tree_big', x, y, 4.6, (5.6, 5.0, 3.2), 77, C, M, subdiv=3, sub=1, trunk_r=0.36)

    print('bed ok')


# ---------------------------------------------------------------- 鍦烘櫙

def prepare_campus():
    bpy.ops.import_scene.gltf(filepath=CAMPUS)
    removed = 0
    for o in list(bpy.data.objects):
        if o.name.startswith('\u5927\u95e8_') or o.name.startswith('\u55b7\u6cc9_'):
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
    for nm, col in (('Material_0', (0.70, 0.665, 0.60)), ('Material_1', (0.80, 0.745, 0.655)),
                    ('Material_70', (0.82, 0.765, 0.670)), ('Material_63', (0.62, 0.60, 0.57)),
                    ('linework_7b5a24_t_0.8', (0.33, 0.33, 0.325)),
                    ('linework_777b72_t_0.82', (0.34, 0.34, 0.335)),
                    ('linework_f4efe1_t_0.8', (0.55, 0.53, 0.49))):
        m = bpy.data.materials.get(nm)
        if m and m.use_nodes:
            b = m.node_tree.nodes.get('Principled BSDF')
            if b:
                b.inputs['Base Color'].default_value = (*col, 1.0)
    print('removed old', removed)


def fix_plaza(M):
    """Rebuild the oval plaza as a clean 91 x 80 m ellipse with tiled stone."""
    for nm in ('\u9ec4\u8272\u7f51\u683c\u692d\u5706\u5e7f\u573a_200',
               '\u9ec4\u8272\u7f51\u683c\u692d\u5706\u5e7f\u573a_201',
               'linework_7b5a24_x1'):
        o = bpy.data.objects.get(nm)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    cx, cy = 239.47, 2.15
    rx, ry = 45.5, 40.0
    n = 96
    verts = [(cx, cy, 0.055)]
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), 0.055))
    faces = [(0, i + 1, (i + 1) % n + 1) for i in range(n)]
    C = coll('PLAZA')
    ob = make('PLAZA_ellipse', verts, faces, M['plaza'], C, recalc=False)
    me = ob.data
    uvl = me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (co.x / 14.4, co.y / 14.4)
    ring_in, ring_out = 0.985, 1.0
    sections = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        sections.append((cx + rx * ring_in * math.cos(a), cy + ry * ring_in * math.sin(a),
                         cx + rx * ring_out * math.cos(a), cy + ry * ring_out * math.sin(a)))
    band_solid('PLAZA_edge', sections, 0.055, 0.085, M['curb'], C, uv=2.0, caps=False)
    print('plaza rebuilt')


def setup_world(M):
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    l = bpy.data.lights.new('SUN', 'SUN'); l.energy = 1.7; l.angle = math.radians(4.0)
    l.color = (1.0, 0.95, 0.88)
    o = bpy.data.objects.new('SUN', l); sc.collection.objects.link(o)
    o.rotation_euler = Vector((-0.62, -0.50, -0.72)).to_track_quat('-Z', 'Y').to_euler()
    # 骞垮満渚цˉ鍏夛紙鎶婂ぇ闂ㄥ唴琛ㄩ潰鎻愪寒锛?
    al = bpy.data.lights.new('FILL', 'AREA'); al.energy = 30000; al.size = 40
    al.color = (0.85, 0.90, 1.0)
    ao = bpy.data.objects.new('FILL', al); sc.collection.objects.link(ao)
    ao.location = (255, -12, 22)
    ao.rotation_euler = (Vector((255, -12, 22)) - Vector((281, 30, 5))).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.66, 0.72, 0.82, 1)
    bg.inputs[1].default_value = 0.85
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = -0.25
    cam = bpy.data.cameras.new('CAM'); cam.lens = 35
    c = bpy.data.objects.new('CAM', cam); sc.collection.objects.link(c)
    sc.camera = c
    c.location = (319, 57, 3.4)
    d = Vector(c.location) - Vector((281, 24.5, 4.8))
    c.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    r = sc.render
    r.engine = 'BLENDER_EEVEE'
    r.resolution_x = 1280
    r.resolution_y = 720
    try:
        sc.eevee.taa_render_samples = 32
    except Exception:
        pass


def main():
    clear_scene()
    M = build_materials()
    prepare_campus()
    fix_plaza(M)
    build_gate(M)
    build_fountain(M)
    build_bed(M)
    setup_world(M)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, '_build', 'xmfls_gate.blend'))
    print('SAVED')


if __name__ == '__main__':
    main()

