# -*- coding: utf-8 -*-
import json, struct, sys, os, math

def load_glb(p):
    d = open(p, 'rb').read()
    assert d[:4] == b'glTF'
    off = 12
    js = None; bin_ = None
    while off < len(d):
        ln, ty = struct.unpack_from('<II', d, off)
        chunk = d[off+8:off+8+ln]
        if ty == 0x4E4F534A:
            js = json.loads(chunk.decode('utf-8'))
        elif ty == 0x004E4942:
            bin_ = chunk
        off += 8 + ln
    return js, bin_

def quat_mat(q):
    x, y, z, w = q
    return [
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
    ]

def trs_matrix(n):
    if 'matrix' in n:
        m = n['matrix']
        # column-major
        return [[m[0], m[4], m[8], m[12]],
                [m[1], m[5], m[9], m[13]],
                [m[2], m[6], m[10], m[14]],
                [m[3], m[7], m[11], m[15]]]
    t = n.get('translation', [0, 0, 0])
    r = n.get('rotation', [0, 0, 0, 1])
    s = n.get('scale', [1, 1, 1])
    R = quat_mat(r)
    M = [[R[i][j] * s[j] for j in range(3)] + [t[i]] for i in range(3)]
    M.append([0, 0, 0, 1])
    return M

def matmul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def xf(M, p):
    return [sum(M[i][j]*p[j] for j in range(3)) + M[i][3] for i in range(3)]

p = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Jim\Downloads\厦门外国语学校（海沧校区）-edited-20261027-1632-edited-20261027-1659.glb'
j, bin_ = load_glb(p)
nodes = j['nodes']
meshes = j['meshes']
accs = j['accessors']

world = {}
def walk(i, parent):
    M = matmul(parent, trs_matrix(nodes[i]))
    world[i] = M
    for c in nodes[i].get('children', []) or []:
        walk(c, M)

scene = j['scenes'][j.get('scene', 0)]
I = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
for r in scene['nodes']:
    walk(r, I)

rows = []
for i, n in enumerate(nodes):
    if 'mesh' not in n:
        continue
    mi = n['mesh']
    bb = [1e18]*3; BB = [-1e18]*3
    for prim in meshes[mi]['primitives']:
        ai = prim['attributes'].get('POSITION')
        if ai is None:
            continue
        acc = accs[ai]
        mn, mx = acc['min'], acc['max']
        for x in (mn[0], mx[0]):
            for y in (mn[1], mx[1]):
                for z in (mn[2], mx[2]):
                    q = xf(world[i], [x, y, z])
                    for k in range(3):
                        bb[k] = min(bb[k], q[k]); BB[k] = max(BB[k], q[k])
    rows.append({
        'i': i, 'name': n.get('name', ''), 'mesh': mi,
        'min': [round(v, 2) for v in bb], 'max': [round(v, 2) for v in BB],
        'size': [round(BB[k]-bb[k], 2) for k in range(3)],
        'center': [round((BB[k]+bb[k])/2, 2) for k in range(3)],
        'tris': sum(accs[pr['indices']]['count']//3 for pr in meshes[mi]['primitives'] if 'indices' in pr),
    })

out = sys.argv[2] if len(sys.argv) > 2 else None
print('total meshes', len(rows))
# overall bounds
mn = [min(r['min'][k] for r in rows) for k in range(3)]
mx = [max(r['max'][k] for r in rows) for k in range(3)]
print('SCENE BOUNDS', [round(v,1) for v in mn], [round(v,1) for v in mx])

kw = ['门', 'gate', '噴', '喷', 'fountain', 'plaza', '广场', '花', 'flower', '校', 'sign', 'wall', '喷泉']
print('--- keyword nodes ---')
for r in rows:
    nm = r['name']
    if any(k.lower() in nm.lower() for k in kw):
        print(r)

print('--- all names ---')
for r in rows:
    print(r['i'], r['name'], 'size', r['size'], 'center', r['center'])

if out:
    json.dump(rows, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
