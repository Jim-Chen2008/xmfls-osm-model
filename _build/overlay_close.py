from pathlib import Path
p=Path(r'xmfls-osm-model\src\style.css'); s=p.read_text(encoding='utf-8')
s=s.replace("#overlayClose{position:absolute;right:10px;top:8px;z-index:2;", "#overlayClose{position:absolute;right:10px;top:8px;z-index:30;")
p.write_text(s,encoding='utf-8'); print('css close')
