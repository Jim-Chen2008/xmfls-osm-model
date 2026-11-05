from pathlib import Path
p=Path(r'xmfls-osm-model\src\calibrate.html'); s=p.read_text(encoding='utf-8')
s=s.replace("const DEFAULTS = { angle:79.7, scale:0.38, ax:-133, az:-35, opacity:0.74 };", "const DEFAULTS = { angle:259.7, scale:0.38, ax:-133, az:-35, opacity:0.74 };")
s=s.replace('id="rot" type="range" min="-180" max="180" step="0.1" value="79.7"', 'id="rot" type="range" min="-180" max="180" step="0.1" value="-100.3"')
s=s.replace('id="rotv">79.7°', 'id="rotv">259.7°')
s=s.replace('R 79.7° / S 0.38', 'R 259.7° / S 0.38')
p.write_text(s,encoding='utf-8'); print('flipped default')
