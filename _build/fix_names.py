# -*- coding: utf-8 -*-
"""Rewrite prepare_campus / fix_plaza with ASCII-safe unicode escapes after an
accidental GBK round-trip corrupted the Chinese literals."""
import io, os

p = r"C:\xmfls test\ds\xmfls-osm-model\_build\build_scene.py"
s = open(p, encoding='utf-8').read()
i0 = s.index('def prepare_campus():')
i1 = s.index('def setup_world(M):')

new = '''def prepare_campus():
    bpy.ops.import_scene.gltf(filepath=CAMPUS)
    removed = 0
    for o in list(bpy.data.objects):
        if o.name.startswith('\\u5927\\u95e8_') or o.name.startswith('\\u55b7\\u6cc9_'):
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
    for nm in ('\\u9ec4\\u8272\\u7f51\\u683c\\u692d\\u5706\\u5e7f\\u573a_200',
               '\\u9ec4\\u8272\\u7f51\\u683c\\u692d\\u5706\\u5e7f\\u573a_201',
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


'''
s = s[:i0] + new + s[i1:]
open(p, 'w', encoding='utf-8').write(s)
print('patched; syntax check:')
import ast
ast.parse(s)
print('syntax ok')
