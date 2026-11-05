from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
line="    addFeature({ kind: '广场', name: '黄色网格广场', x: plazaX, z: plazaZ, y: 2, angle: 0, layer: G.landmarks });\n"
if line not in s: raise SystemExit('plaza feature line missing')
s=s.replace(line,'')
anchor="  addFeature({ kind: '边界', name: '校园边界', x: 0, z: -153, y: 2, angle: 0, layer: G.ground });"
if anchor not in s: raise SystemExit('boundary missing')
s=s.replace(anchor, anchor+"\n  addFeature({ kind: '广场', name: '黄色网格广场', x: 130.5, z: -80.03, y: 2, angle: 0, layer: G.landmarks });")
p.write_text(s,encoding='utf-8')
html=Path(r'xmfls-osm-model\src\index.html'); h=html.read_text(encoding='utf-8')
h=h.replace('<div><b>31</b><span>编号对象</span></div>','<div><b>32</b><span>编号对象</span></div>')
h=h.replace('<span id="indexCount">31</span>','<span id="indexCount">32</span>')
html.write_text(h,encoding='utf-8')
print('renumbered')
