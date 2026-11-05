from pathlib import Path
p = Path(r'xmfls-osm-model\src\app.js')
s = p.read_text(encoding='utf-8')
block = Path(r'xmfls-osm-model\_build\features_geometry_block.js').read_text(encoding='utf-8')
anchor = "  for (const b of DATA.buildings) makeBuilding(b, b.inside);\n  G.outside.visible = false;"
if anchor not in s:
    raise SystemExit('building anchor missing')
s = s.replace(anchor, anchor + "\n\n" + block)
p.write_text(s, encoding='utf-8')
print('features geometry inserted')
