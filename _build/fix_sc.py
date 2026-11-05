from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("  const sc = DATA.school;\n  addLabel(sc.name || '学校', 0, 28, 0, 'school');", "  const schoolRec = DATA.school;\n  addLabel(schoolRec.name || '学校', 0, 28, 0, 'school');")
p.write_text(s,encoding='utf-8')
print('patched')
