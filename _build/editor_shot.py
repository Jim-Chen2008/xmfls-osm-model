from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
(base/'inspect_editor.html').write_text(html.replace('</body>','<script>setTimeout(function(){document.querySelector("#editToggle").click();},800);</script></body>'),encoding='utf-8')
print('ok')
