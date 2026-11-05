from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.focusFeature(M.FEATURES.find(f=>f.name.indexOf('椭圆')>=0));},700);</script>'''
(base/'inspect_plaza.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
