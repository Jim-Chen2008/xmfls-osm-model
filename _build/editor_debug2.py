from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("window.__MODEL = { scene, camera, renderer, view, fly, buildingViews, showBuilding, G, sun, FEATURES, focusFeature, height: () => height };", "window.__MODEL = { scene, camera, renderer, view, fly, buildingViews, showBuilding, G, sun, FEATURES, focusFeature, EDIT, setEditorMode, selectEditTarget, exportEdits, importEdits, height: () => height };")
p.write_text(s,encoding='utf-8')
base=Path(r'xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.setEditorMode(true); M.selectEditTarget(M.EDIT.targets.find(t=>t.id==='17'));},800);</script>'''
(base/'inspect_editor2.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
