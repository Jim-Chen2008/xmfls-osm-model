from pathlib import Path
html=Path(r'xmfls-osm-model\src\index.html').read_text(encoding='utf-8')
js='''<style>#dbg{position:fixed;z-index:99;left:20px;top:170px;background:rgba(20,30,24,.9);color:#cfe3c9;font:11px monospace;padding:10px;white-space:pre;line-height:1.5}</style>
<script>
setTimeout(function(){
 var M=window.__MODEL; if(!M)return; var el=M.renderer.domElement; el.setPointerCapture=function(){}; el.releasePointerCapture=function(){};
 var y0=M.fly.yaw, p0=M.fly.pitch;
 el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId:1,pointerType:'mouse',button:0,clientX:600,clientY:400}));
 for(var i=1;i<=10;i++) el.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,pointerId:1,pointerType:'mouse',buttons:1,clientX:600+i*15,clientY:400-i*8}));
 el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId:1,pointerType:'mouse',button:0,clientX:750,clientY:320}));
 var d=document.createElement('div'); d.id='dbg'; d.textContent='yaw '+y0.toFixed(3)+' -> '+M.fly.yaw.toFixed(3)+'\\npitch '+p0.toFixed(3)+' -> '+M.fly.pitch.toFixed(3)+'\\nleft-drag test'; document.body.appendChild(d);
},700);
</script>'''
Path(r'xmfls-osm-model\src\inspect_drag.html').write_text(html.replace('</body>',js+'</body>'),encoding='utf-8')
print('ok')
