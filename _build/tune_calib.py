from pathlib import Path
p=Path(r'xmfls-osm-model\src\calibrate.html'); s=p.read_text(encoding='utf-8')
s=s.replace("const IMG_ANCHOR = { x:720, y:410 };\n  const DEFAULTS = { angle:79.7, scale:0.64, ax:-133, az:-35, opacity:0.72 };", "const IMG_ANCHOR = { x:610, y:300 };\n  const DEFAULTS = { angle:79.7, scale:0.38, ax:-133, az:-35, opacity:0.74 };")
s=s.replace("id=\"scl\" type=\"range\" min=\"0.2\" max=\"1.5\" step=\"0.005\" value=\"0.64\"", "id=\"scl\" type=\"range\" min=\"0.2\" max=\"1.5\" step=\"0.005\" value=\"0.38\"")
s=s.replace("id=\"sclv\">0.640", "id=\"sclv\">0.380")
s=s.replace("R 79.7° / S 0.64", "R 79.7° / S 0.38")
p.write_text(s,encoding='utf-8'); print('tuned')
