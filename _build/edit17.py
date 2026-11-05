from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.setEditorMode(true); var t=M.EDIT.targets.find(t=>t.id==='17'); M.selectEditTarget(t); function set(id,v){var e=document.querySelector(id); e.value=v; e.dispatchEvent(new Event('input',{bubbles:true})); e.dispatchEvent(new Event('change',{bubbles:true}));} set('#edX',-105); set('#edH',25);},900);</script>'''
(base/'inspect_edit17.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
