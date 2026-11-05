from pathlib import Path
html=Path(r'xmfls-osm-model\src\index.html').read_text(encoding='utf-8')
js='''<style>#dbg{position:fixed;z-index:99;left:20px;top:170px;background:rgba(20,30,24,.9);color:#cfe3c9;font:11px monospace;padding:10px;white-space:pre;line-height:1.5}</style>
<script>
setTimeout(function(){
 var M=window.__MODEL; if(!M)return;
 var start=M.camera.position.clone();
 window.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyW',key:'w',bubbles:true}));
 window.dispatchEvent(new KeyboardEvent('keydown',{code:'Space',key:' ',bubbles:true}));
 var d=document.createElement('div'); d.id='dbg'; document.body.appendChild(d);
 setTimeout(function(){
  window.dispatchEvent(new KeyboardEvent('keyup',{code:'KeyW',key:'w',bubbles:true}));
  window.dispatchEvent(new KeyboardEvent('keyup',{code:'Space',key:' ',bubbles:true}));
  var p=M.camera.position;
  d.textContent='start  '+start.x.toFixed(1)+', '+start.y.toFixed(1)+', '+start.z.toFixed(1)+'\\nnow    '+p.x.toFixed(1)+', '+p.y.toFixed(1)+', '+p.z.toFixed(1)+'\\nyaw '+M.fly.yaw.toFixed(2)+'  pitch '+M.fly.pitch.toFixed(2)+'\\nWASD/Space keys tested';
 },1500);
},600);
</script>'''
Path(r'xmfls-osm-model\src\inspect_move.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
