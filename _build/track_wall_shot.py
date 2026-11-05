from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.setEditorMode(true); M.selectEditTarget(M.EDIT.targets.find(t=>t.id==='22'));},900);</script>'''
(base/'inspect_edit_track.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
js2='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.setEditorMode(true); M.selectEditTarget(M.EDIT.targets.find(t=>t.id==='33'));},900);</script>'''
(base/'inspect_edit_wall.html').write_text(html.replace('</body>',js2+'</body>'),encoding='utf-8')
print('ok')
