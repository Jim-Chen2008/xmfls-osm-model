from pathlib import Path
base=Path('xmfls-osm-model/src'); html=(base/'index.html').read_text(encoding='utf-8')
js='''<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.camera.position.set(190,12,-155); var tx=136,ty=5,tz=-110; var dx=tx-190,dy=ty-12,dz=tz+155; var L=Math.hypot(dx,dy,dz); M.fly.yaw=Math.atan2(-dx,-dz); M.fly.pitch=Math.asin(dy/L); M.camera.rotation.set(M.fly.pitch,M.fly.yaw,0,'YXZ'); M.G.guide.visible=true;},700);</script>'''
(base/'inspect_gate_elev.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
