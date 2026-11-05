from pathlib import Path
p=Path(r'xmfls-osm-model\src\calibrate.html'); s=p.read_text(encoding='utf-8')
s=s.replace("angle:79.7", "angle:259.7").replace("value=\"79.7\"", "value=\"-100.3\"")
s=s.replace("R 79.7° / S 0.38", "R 259.7° / S 0.38")
Path(r'xmfls-osm-model\src\calib_flip_test.html').write_text(s,encoding='utf-8')
print('ok')
