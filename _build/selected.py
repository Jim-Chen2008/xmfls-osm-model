from pathlib import Path
html=Path(r'xmfls-osm-model\src\index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; var rec=M.buildingViews.find(function(v){return v.inside;}).rec; M.showBuilding(rec); var s=document.getElementById('heightSlider'); s.value=18; s.dispatchEvent(new Event('input',{bubbles:true}));},700);</script>'''
Path(r'xmfls-osm-model\src\inspect_selected.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
