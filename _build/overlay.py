from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.setEditorMode(true); document.querySelector('#overlayBtn').click();},900);</script>'''
(base/'inspect_overlay.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
