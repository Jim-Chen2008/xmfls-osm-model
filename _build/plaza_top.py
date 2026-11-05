from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
style='<style>.map-label,#coordsHud{display:none!important}</style>'
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.camera.position.set(121,90,-87); M.fly.yaw=0; M.fly.pitch=-Math.PI/2+0.02; M.camera.rotation.set(M.fly.pitch,M.fly.yaw,0,'YXZ');},700);</script>'''
(base/'inspect_plaza_top.html').write_text(html.replace('</head>',style+'</head>').replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
