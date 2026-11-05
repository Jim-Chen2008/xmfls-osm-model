from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("  try {\n    renderer.render(scene, camera);", "  window.__MODEL = { scene, camera, renderer, view, buildingViews, showBuilding, G, height: () => height };\n\n  try {\n    renderer.render(scene, camera);")
p.write_text(s,encoding='utf-8')
html=Path(r'xmfls-osm-model\src\index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.view.goalTarget.set(20,4,-20); M.view.goalRadius=220; M.view.goalPhi=1.18; M.view.goalTheta=.72; M.view.auto=false;},700);</script>'''
(Path(r'xmfls-osm-model\src\inspect_close.html')).write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
