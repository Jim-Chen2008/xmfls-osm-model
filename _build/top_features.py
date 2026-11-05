from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var b=document.querySelector('[data-view="top"]'); if(b)b.click();},700);</script>'''
(base/'inspect_top_features.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
