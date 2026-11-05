from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
anchor="  const plazaFeat = addFeature({ kind: '广场', name: '黄色网格椭圆广场', x: 99.13, z: -80.445, y: 2, angle: 50.97, layer: G.landmarks });\n  plazaFeat.group = plazaGroup;"
if anchor not in s: raise SystemExit('plaza feat anchor')
wall=anchor+r'''

  // 33: editable boundary wall
  const wallGroup = new THREE.Group();
  G.context.add(wallGroup);
  {
    const poly = DATA.school.polygon;
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length];
      const dx = b[0] - a[0], dz = b[1] - a[1];
      const len = Math.hypot(dx, dz);
      if (len < .2) continue;
      const mx = (a[0] + b[0]) / 2, mz = (a[1] + b[1]) / 2;
      const ry = Math.atan2(-dz, dx);
      lmBox(len, 2.3, .45, LMAT.concrete, mx, 1.15, mz, wallGroup, ry);
    }
    const wf = addFeature({ kind: '围墙', name: '校园围墙', x: 0, z: -153, y: 4, angle: 0, layer: G.context });
    wf.group = wallGroup;
  }
'''
s=s.replace(anchor,wall)
p.write_text(s,encoding='utf-8')
# counts
h=Path(r'xmfls-osm-model\src\index.html'); t=h.read_text(encoding='utf-8')
t=t.replace('<div><b>32</b><span>编号对象</span></div>','<div><b>33</b><span>编号对象</span></div>')
t=t.replace('<span id="indexCount">32</span>','<span id="indexCount">33</span>')
h.write_text(t,encoding='utf-8')
# calibration key add wall
c=Path(r'xmfls-osm-model\src\calibrate.html'); cc=c.read_text(encoding='utf-8')
cc=cc.replace("{no:'32', name:'黄网格椭圆广场', x:99.13, z:-80.445}", "{no:'32', name:'黄网格椭圆广场', x:99.13, z:-80.445},\n    {no:'33', name:'围墙', x:0, z:-153}")
c.write_text(cc,encoding='utf-8')
print('wall added')
