from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.setEditorMode(true); M.selectEditTarget(M.EDIT.targets.find(t=>t.id==='32'));},900);</script>'''
(base/'inspect_ellipse_edit.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
