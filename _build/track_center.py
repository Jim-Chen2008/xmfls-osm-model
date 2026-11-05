from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("x: outerC[0] + TRACK_SHIFT_X, z: outerC[1] + 23, y: 2.4, angle: CAMPUS_BEARING", "x: outerC[0] + TRACK_SHIFT_X, z: outerC[1], y: 2.4, angle: CAMPUS_BEARING")
p.write_text(s,encoding='utf-8'); print('track center')
