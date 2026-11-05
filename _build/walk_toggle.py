from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("    if (name === 'walk') { enterWalk(); return; }", "    if (name === 'walk') { if (WALK.active) leaveWalk(true); else enterWalk(); return; }")
p.write_text(s,encoding='utf-8'); print('toggle fixed')
