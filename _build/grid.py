from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("grid.position.y = .018;", "grid.position.y = .026;")
s=s.replace("grid.material.opacity = .28;", "grid.material.opacity = .38;")
p.write_text(s,encoding='utf-8')
print('grid patched')
