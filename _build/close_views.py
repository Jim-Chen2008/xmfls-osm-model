from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
for name,js in {
 'inspect_tennis.html':"M.focusFeature(M.FEATURES.find(f=>f.name==='网球场 A'));",
 'inspect_trackland.html':"M.focusFeature(M.FEATURES.find(f=>f.name==='台下平台 · 膜结构'));",
 'inspect_gate.html':"M.focusFeature(M.FEATURES.find(f=>f.name==='大门'));"
}.items():
    script=f'<script>setTimeout(function(){{var M=window.__MODEL; if(!M)return; {js}}},700);</script>'
    (base/name).write_text(html.replace('</body>',script+'</body>'),encoding='utf-8')
print('ok')
