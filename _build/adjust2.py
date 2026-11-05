from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("    const z0 = bball.bbox[2], z1 = bball.bbox[3];\n    const x0 = -73, x1 = -19;", "    const z0 = -94, z1 = -1;\n    const x0 = -73, x1 = -19;")
s=s.replace("    const wide = f.kind === '场地' || f.kind === '球场' || f.kind === '边界';\n    const off = wide ? 155 : (f.kind === '建筑' ? 68 : 48);\n    const targetY = f.kind === '建筑' ? Math.min(height * .5, 7) : 2.2;\n    camera.position.set(f.x + off * .66, Math.max(26, off * .55), f.z + off * .66);", "    const wide = f.kind === '场地' || f.kind === '球场' || f.kind === '边界';\n    const off = wide ? 220 : (f.kind === '建筑' ? 100 : 95);\n    const targetY = f.kind === '建筑' ? Math.min(height * .5, 7) : 2.2;\n    camera.position.set(f.x + off * .75, Math.max(55, off * .6), f.z + off * .75);")
p.write_text(s,encoding='utf-8')
css=Path(r'xmfls-osm-model\src\style.css'); c=css.read_text(encoding='utf-8')
c=c.replace(".idx-row:hover{background:rgba(67,78,67,.055)}", ".idx-row:hover{background:rgba(67,78,67,.055)}\n.idx-row.active{background:rgba(164,83,55,.09)}")
css.write_text(c,encoding='utf-8')
print('patched')
