# -*- coding: utf-8 -*-
"""Replace build_gate() with the 4-block composition matching the site photos."""
import io, re, os

p = os.path.join(os.path.dirname(__file__), 'build_scene.py')
s = open(p, encoding='utf-8').read()

start = s.index("    H, T = 9.2, 1.2")
end = s.index("    print('gate objects', len(objs))")
new = '''    H, T = 9.4, 1.2
    OW, OH = 13.5, 5.6             # 中央门洞
    BW, GW, EW = 5.25, 3.15, 4.0   # 内墩宽 / 侧门净宽 / 外墩宽
    uo = OW / 2.0                  # 6.75
    u2 = uo + BW                   # 12.00
    u3 = u2 + GW                   # 15.15
    u4 = u3 + EW                   # 19.15

    # ---------- 后侧高墙（跨两内墩，墩后）
    WY0, WY1 = 0.15, 1.35
    add(box('GATE_wall', -u2, u2, WY0, WY1, OH, H, M['panel'], C, uv=4.8))
    add(box('GATE_wall_coping', -u2 - 0.06, u2 + 0.06, WY0 - 0.08, WY1 + 0.08, H, H + 0.16, M['coping'], C))
    add(box('GATE_wall_shadow', -u2, u2, WY0 - 0.03, WY0, OH, OH + 0.10, M['stone_dark'], C))
    for sgn in (-1, 1):
        add(box('GATE_wall_end_%d' % sgn, min(sgn * u2, sgn * (u2 + 0.12)), max(sgn * u2, sgn * (u2 + 0.12)),
                WY0, WY1, OH, H, M['panel'], C, uv=4.8))

    # 金色字（街道面）
    chars = '厦门外国语学校'
    pitch = 1.86
    for i, ch in enumerate(chars):
        t = text_mesh('GATE_txt_%d' % i, ch, 'C:/Windows/Fonts/STXINGKA.TTF', 1.55, C, extrude=0.05)
        t.location = ((len(chars) - 1) / 2.0 * pitch - i * pitch, WY1 + 0.02, 7.60)
        t.rotation_euler = (math.radians(90), 0, math.pi)
        t.data.materials.append(M['gold'])
        add(t)
    for w, dx in [('XIAMEN', 3.55), ('FOREIGN', 1.35), ('LANGUAGE', -0.95), ('SCHOOL', -3.20)]:
        t = text_mesh('GATE_en_%s' % w, w, 'C:/Windows/Fonts/calibril.ttf', 0.42, C, extrude=0.03, spacing=1.15)
        t.location = (dx, WY1 + 0.02, 6.72)
        t.rotation_euler = (math.radians(90), 0, math.pi)
        t.data.materials.append(M['gold'])
        add(t)

    # ---------- 四块门墩
    for sgn in (-1, 1):
        # 内墩（承墙）
        a, b = sorted((sgn * uo, sgn * u2))
        add(box('GATE_blk_in_%d' % sgn, a, b, -3.90, 0.35, 0, OH, M['panel'], C, uv=4.8))
        add(box('GATE_blk_in_cap_%d' % sgn, a - 0.06, b + 0.06, -3.98, 0.42, OH, OH + 0.14, M['coping'], C))
        add(box('GATE_blk_in_base_%d' % sgn, a, b, -3.92, 0.35, 0, 0.12, M['stone_dark'], C))
        # 门洞
        du = sgn * (uo + 2.25)
        d0, d1 = min(du - 0.55, du + 0.55), max(du - 0.55, du + 0.55)
        add(box('GATE_door_in_%d' % sgn, d0, d1, -3.96, -3.90, 0.02, 2.35, M['door'], C))
        add(box('GATE_doortop_in_%d' % sgn, d0 - 0.14, d1 + 0.14, -3.98, -3.88, 2.35, 2.47, M['stone'], C))
        for kk in range(2):
            y1 = -3.90 - 0.30 * (kk + 1)
            add(box('GATE_step_in_%d_%d' % (sgn, kk), du - 1.0, du + 1.0, y1, y1 + 0.30, 0, 0.15 * (2 - kk), M['stone'], C))
        # 小窗
        w0 = min(du + sgn * 0.85, du + sgn * 1.55)
        w1 = max(du + sgn * 0.85, du + sgn * 1.55)
        add(box('GATE_win_in_%d' % sgn, w0, w1, -3.94, -3.89, 3.15, 3.60, M['glass'], C))
        # 外墩
        a, b = sorted((sgn * u3, sgn * u4))
        add(box('GATE_blk_out_%d' % sgn, a, b, -3.40, 0.35, 0, 4.40, M['panel'], C, uv=4.8))
        add(box('GATE_blk_out_cap_%d' % sgn, a - 0.06, b + 0.06, -3.48, 0.42, 4.40, 4.54, M['coping'], C))
        add(box('GATE_blk_out_base_%d' % sgn, a, b, -3.42, 0.35, 0, 0.12, M['stone_dark'], C))
        du2 = sgn * (u3 + 1.35)
        o0, o1 = min(du2 - 0.9, du2 + 0.9), max(du2 - 0.9, du2 + 0.9)
        add(box('GATE_door_out_%d' % sgn, o0, o1, -3.46, -3.40, 0.02, 2.55, M['door'], C))
        add(box('GATE_doortop_out_%d' % sgn, o0 - 0.12, o1 + 0.12, -3.48, -3.38, 2.55, 2.66, M['stone'], C))

        # 侧门（折叠门）
        g0, g1 = sorted((sgn * u2, sgn * u3))
        add(box('GATE_sg_top_%d' % sgn, g0 + 0.05, g1 - 0.05, -0.02, 0.04, 1.50, 1.56, M['steel'], C))
        add(box('GATE_sg_bot_%d' % sgn, g0 + 0.05, g1 - 0.05, -0.02, 0.04, 0.06, 0.12, M['steel'], C))
        x = g0 + 0.1
        k = 0
        while x < g1 - 0.2:
            add(bar('GATE_sg_x1_%d_%d' % (sgn, k), (x, 0.06), (x + 0.45, 1.52), 0.035, 0.035, M['steel'], C))
            add(bar('GATE_sg_x2_%d_%d' % (sgn, k), (x + 0.45, 0.06), (x, 1.52), 0.035, 0.035, M['steel'], C))
            x += 0.45
            k += 1

        # 摄像机（内墩洞口边）
        cx0 = sgn * (uo + 0.25)
        cx1 = sgn * (uo + 0.65)
        add(box('GATE_cam_arm_%d' % sgn, min(cx0, cx1), max(cx0, cx1), -3.95, -3.88, 4.72, 4.78, M['white'], C))
        add(box('GATE_cam_box_%d' % sgn, min(cx0, cx1) - 0.10, max(cx0, cx1) + 0.10, -4.10, -3.88, 4.56, 4.76, M['white'], C))

    # ---------- 中央门洞推拉门
    add(box('GATE_mg_top', -uo + 0.1, uo - 0.1, -0.02, 0.04, 1.40, 1.46, M['steel'], C))
    add(box('GATE_mg_bot', -uo + 0.1, uo - 0.1, -0.02, 0.04, 0.06, 0.12, M['steel'], C))
    x = -uo + 0.2
    k = 0
    while x < uo - 0.3:
        add(bar('GATE_mg_x1_%d' % k, (x, 0.06), (x + 0.55, 1.42), 0.032, 0.032, M['steel'], C))
        add(bar('GATE_mg_x2_%d' % k, (x + 0.55, 0.06), (x, 1.42), 0.032, 0.032, M['steel'], C))
        x += 0.55
        k += 1

    # ---------- 街道侧 / 校内地面
    add(box('GATE_street_lawn', -36, 36, 1.9, 5.0, 0, 0.07, M['lawn'], C, uv=3.0))
    add(box('GATE_street_walk', -36, 36, 5.0, 7.6, 0, 0.10, M['grey'], C, uv=2.0))
    add(box('GATE_street_road', -36, 36, 7.6, 17.0, 0, 0.05, M['asphalt'], C, uv=6.0))
    add(box('GATE_road_curb', -36, 36, 7.4, 7.65, 0, 0.14, M['curb'], C, uv=2.0))
    add(box('GATE_inner_apron', -32.0, 32.0, -5.2, -3.95, 0, 0.05, M['grey'], C, uv=2.0))

'''
s = s[:start] + new + s[end:]
open(p, 'w', encoding='utf-8').write(s)
print('patched build_gate; new length', len(s))
