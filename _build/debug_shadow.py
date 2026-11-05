from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("window.__MODEL = { scene, camera, renderer, view, buildingViews, showBuilding, G, height: () => height };", "window.__MODEL = { scene, camera, renderer, view, buildingViews, showBuilding, G, sun, height: () => height };")
p.write_text(s,encoding='utf-8')
html=Path(r'xmfls-osm-model\src\index.html').read_text(encoding='utf-8')
js='''<style>#dbg{position:fixed;z-index:99;left:10px;bottom:10px;background:#000;color:#0f0;font:11px monospace;padding:8px;white-space:pre}</style>
<script>setTimeout(function(){var M=window.__MODEL; if(!M)return; M.scene.background=new THREE.Color(0x3a5058); var cube=new THREE.Mesh(new THREE.BoxGeometry(35,55,35),new THREE.MeshStandardMaterial({color:0xcc4433,roughness:.7})); cube.position.set(0,27.5,0); cube.castShadow=true; cube.receiveShadow=true; M.scene.add(cube); M.view.goalTarget.set(10,8,-10); M.view.goalRadius=260; M.view.goalPhi=1.18; M.view.goalTheta=.72; M.view.auto=false; var info='sun '+M.sun.intensity+' cast '+M.sun.castShadow+' shadowmap '+M.renderer.shadowMap.enabled+'\\n'; M.buildingViews.forEach(function(v,i){ if(i<4) info+=v.rec.id+' children='+v.group.children.length+' roofs='+v.group.children.filter(function(c){return c.type==='Mesh'}).length+'\\n'; }); var d=document.createElement('div'); d.id='dbg'; d.textContent=info; document.body.appendChild(d);},700);</script>'''
(Path(r'xmfls-osm-model\src\inspect_debug.html')).write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
