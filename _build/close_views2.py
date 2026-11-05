from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
for name,expr in {'inspect_grand.html':"M.focusFeature(M.FEATURES.find(f=>f.name==='主席台（南看台）'));",'inspect_bball.html':"M.focusFeature(M.FEATURES.find(f=>f.name==='篮球场 ×6'));"}.items():
    (base/name).write_text(html.replace('</body>',f'<script>setTimeout(function(){{var M=window.__MODEL; if(!M)return; {expr}}},700);</script></body>'),encoding='utf-8')
print('ok')
