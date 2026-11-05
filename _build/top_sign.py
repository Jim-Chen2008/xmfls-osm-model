from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
for name,delta in [('inspect_top_plus.html',0.1798),('inspect_top_minus.html',-0.1798)]:
    js=f'''<script>setTimeout(function(){{var M=window.__MODEL; if(!M)return; document.querySelector('[data-view="top"]').click(); M.fly.yaw += {delta};}},900);</script>'''
    (base/name).write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
