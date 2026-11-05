# -*- coding: utf-8 -*-
"""Rebuild the gate as: central portal + per side [gatehouse][tall block][car gate][end block]."""
import os

p = os.path.join(os.path.dirname(__file__), 'build_scene.py')
s = open(p, encoding='utf-8').read()
start = s.index("    H, T = 9.4, 1.2")
end = s.index("    print('gate objects', len(objs))")

new = '''    H = 9.4
    OW = 13.5                         # 中央门洞
    GH_W, GH_H = 5.2, 4.5             # 门卫房墩
    TB_W, TB_H = 6.3, 6.0             # 高墩
    CG_W, CG_H = 2.8, 3.4             # 汽车侧门
    EB_W, EB_H = 4.1, 3.6             # 端墩
    u1 = OW / 2.0                     # 6.75
    u2 = u1 + GH_W                    # 11.95
    u3 = u2 + TB_W                    # 18.25
    u4 = u3 + CG_W                    # 21.05
    u5 = u4 + EB_W                    # 25.15
    WY0, WY1 = 0.15, 1.35
    WB = 5.6                          # 高墙底标高

    # ---------- 横墙（跨中央门洞 + 两侧门卫房）
    add(box('GATE_wall', -u2, u2, WY0, WY1, WB, H, M['panel'], C, uv=4.8))
    add(box('GATE_wall_coping', -u2 - 0.06, u2 + 0.06, WY0 - 0.08, WY1 + 0.08, H, H + 0.16, M['coping'], C))
    add(box('GATE_wall_soffit', -u2, u2, WY0 - 0.02, WY1 + 0.02, WB, WB + 0.14, M['stone_dark'], C))

    # ---------- 金色字
    chars = '厦门外国语学校'
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

    # ---------- 两侧门墩组
    for sgn in (-1, 1):
        # 1) 门卫房墩
        a, b = sorted((sgn * u1, sgn * u2))
        add(box('GATE_gh_%d' % sgn, a, b, -2.90, 0.35, 0, GH_H, M['panel'], C, uv=4.8))
        add(box('GATE_gh_cap_%d' % sgn, a - 0.06, b + 0.06, -2.98, 0.42, GH_H, GH_H + 0.14, M['coping'], C))
        add(box('GATE_gh_base_%d' % sgn, a, b, -2.92, 0.35, 0, 0.12, M['stone_dark'], C))
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
        # 摄像机（高墙下沿）
        cx0, cx1 = sgn * (u1 + 0.20), sgn * (u1 + 0.55)
        add(box('GATE_cam_%d' % sgn, min(cx0, cx1), max(cx0, cx1), -2.98, -2.90, 4.75, 4.88, M['white'], C))

        # 2) 高墩
        a, b = sorted((sgn * u2, sgn * u3))
        add(box('GATE_tb_%d' % sgn, a, b, -2.20, 0.35, 0, TB_H, M['panel'], C, uv=4.8))
        add(box('GATE_tb_cap_%d' % sgn, a - 0.06, b + 0.06, -2.28, 0.42, TB_H, TB_H + 0.14, M['coping'], C))
        add(box('GATE_tb_base_%d' % sgn, a, b, -2.22, 0.35, 0, 0.12, M['stone_dark'], C))

        # 3) 汽车侧门
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

        # 4) 端墩
        a, b = sorted((sgn * u4, sgn * u5))
        add(box('GATE_eb_%d' % sgn, a, b, -1.60, 0.35, 0, EB_H, M['panel'], C, uv=4.8))
        add(box('GATE_eb_cap_%d' % sgn, a - 0.06, b + 0.06, -1.68, 0.42, EB_H, EB_H + 0.14, M['coping'], C))
        add(box('GATE_eb_base_%d' % sgn, a, b, -1.62, 0.35, 0, 0.12, M['stone_dark'], C))
        o0, o1 = sorted((sgn * (u4 + 0.7), sgn * (u4 + 2.4)))
        add(box('GATE_eb_door_%d' % sgn, o0, o1, -1.66, -1.60, 0.02, 2.40, M['door'], C))

    # ---------- 中央推拉门
    add(box('GATE_mg_top', -u1 + 0.1, u1 - 0.1, -0.02, 0.04, 1.42, 1.48, M['steel'], C))
    add(box('GATE_mg_bot', -u1 + 0.1, u1 - 0.1, -0.02, 0.04, 0.06, 0.12, M['steel'], C))
    x = -u1 + 0.2
    k = 0
    while x < u1 - 0.3:
        add(bar('GATE_mg_x1_%d' % k, (x, 0.06), (x + 0.55, 1.44), 0.032, 0.032, M['steel'], C))
        add(bar('GATE_mg_x2_%d' % k, (x + 0.55, 0.06), (x, 1.44), 0.032, 0.032, M['steel'], C))
        x += 0.55
        k += 1

    # ---------- 街道侧 / 校内地面
    add(box('GATE_street_lawn', -36, 36, 1.9, 5.0, 0, 0.07, M['lawn'], C, uv=3.0))
    add(box('GATE_street_walk', -36, 36, 5.0, 7.6, 0, 0.10, M['grey'], C, uv=2.0))
    add(box('GATE_street_road', -36, 36, 7.6, 17.0, 0, 0.05, M['asphalt'], C, uv=6.0))
    add(box('GATE_road_curb', -36, 36, 7.4, 7.65, 0, 0.14, M['curb'], C, uv=2.0))
    add(box('GATE_inner_apron', -32.0, 32.0, -4.4, -2.95, 0, 0.05, M['grey'], C, uv=2.0))

'''
s = s[:start] + new + s[end:]
open(p, 'w', encoding='utf-8').write(s)
print('gate patched')
